"""
Metrics collection service for tracking system performance and business metrics.
Collects and stores metrics for analytics and monitoring.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricCategory(Enum):
    """Categories of metrics."""
    SYSTEM = "system"
    API = "api"
    CALL = "call"
    SPEECH = "speech"
    BUSINESS = "business"
    USER = "user"


class Metric(BaseModel):
    """Model for a metric data point."""
    name: str
    type: MetricType
    category: MetricCategory
    value: Union[int, float]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricsCollector:
    """Service for collecting and storing metrics."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.metrics_collection = database.metrics
        self.aggregated_metrics_collection = database.aggregated_metrics
        
        # In-memory counters for performance
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._timers: Dict[str, List[float]] = {}
        
        # Background task for periodic aggregation
        self._aggregation_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the metrics collector and background tasks."""
        self._running = True
        self._aggregation_task = asyncio.create_task(self._periodic_aggregation())
        logger.info("Metrics collector started")
    
    async def stop(self):
        """Stop the metrics collector."""
        self._running = False
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")
    
    # Counter methods
    async def increment_counter(
        self,
        name: str,
        category: MetricCategory,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric."""
        key = self._get_metric_key(name, tags or {})
        self._counters[key] = self._counters.get(key, 0) + value
        
        # Also store individual data point
        await self._store_metric(Metric(
            name=name,
            type=MetricType.COUNTER,
            category=category,
            value=value,
            tags=tags or {}
        ))
    
    async def set_gauge(
        self,
        name: str,
        category: MetricCategory,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Set a gauge metric value."""
        key = self._get_metric_key(name, tags or {})
        self._gauges[key] = value
        
        await self._store_metric(Metric(
            name=name,
            type=MetricType.GAUGE,
            category=category,
            value=value,
            tags=tags or {}
        ))
    
    async def record_histogram(
        self,
        name: str,
        category: MetricCategory,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a value in a histogram."""
        key = self._get_metric_key(name, tags or {})
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        
        await self._store_metric(Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            category=category,
            value=value,
            tags=tags or {}
        ))
    
    async def record_timer(
        self,
        name: str,
        category: MetricCategory,
        duration: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a timer duration."""
        key = self._get_metric_key(name, tags or {})
        if key not in self._timers:
            self._timers[key] = []
        self._timers[key].append(duration)
        
        await self._store_metric(Metric(
            name=name,
            type=MetricType.TIMER,
            category=category,
            value=duration,
            tags=tags or {}
        ))
    
    # Business metrics
    async def track_call_initiated(self, call_id: str, direction: str, language: str):
        """Track call initiation."""
        await self.increment_counter(
            "calls_initiated_total",
            MetricCategory.CALL,
            tags={"direction": direction, "language": language}
        )
        
        await self.increment_counter(
            "calls_total",
            MetricCategory.BUSINESS,
            tags={"status": "initiated", "direction": direction}
        )
    
    async def track_call_completed(
        self,
        call_id: str,
        duration: float,
        status: str,
        language: str,
        qualification_completed: bool
    ):
        """Track call completion."""
        await self.increment_counter(
            "calls_completed_total",
            MetricCategory.CALL,
            tags={"status": status, "language": language}
        )
        
        await self.record_timer(
            "call_duration_seconds",
            MetricCategory.CALL,
            duration,
            tags={"status": status, "language": language}
        )
        
        if qualification_completed:
            await self.increment_counter(
                "calls_qualified_total",
                MetricCategory.BUSINESS,
                tags={"language": language}
            )
    
    async def track_call_failed(self, call_id: str, reason: str, language: str):
        """Track call failure."""
        await self.increment_counter(
            "calls_failed_total",
            MetricCategory.CALL,
            tags={"reason": reason, "language": language}
        )
    
    async def track_handoff(self, call_id: str, reason: str, language: str):
        """Track handoff to human expert."""
        await self.increment_counter(
            "handoffs_total",
            MetricCategory.BUSINESS,
            tags={"reason": reason, "language": language}
        )
    
    async def track_sentiment(self, call_id: str, sentiment_score: float, language: str):
        """Track sentiment analysis results."""
        await self.record_histogram(
            "sentiment_score",
            MetricCategory.BUSINESS,
            sentiment_score,
            tags={"language": language}
        )
        
        # Categorize sentiment
        if sentiment_score > 0.3:
            sentiment_category = "positive"
        elif sentiment_score < -0.3:
            sentiment_category = "negative"
        else:
            sentiment_category = "neutral"
        
        await self.increment_counter(
            "sentiment_distribution",
            MetricCategory.BUSINESS,
            tags={"category": sentiment_category, "language": language}
        )
    
    async def track_speech_processing(
        self,
        operation: str,  # "asr" or "tts"
        duration: float,
        success: bool,
        language: str,
        confidence: Optional[float] = None
    ):
        """Track speech processing metrics."""
        status = "success" if success else "failure"
        
        await self.record_timer(
            f"speech_{operation}_duration_seconds",
            MetricCategory.SPEECH,
            duration,
            tags={"status": status, "language": language}
        )
        
        await self.increment_counter(
            f"speech_{operation}_requests_total",
            MetricCategory.SPEECH,
            tags={"status": status, "language": language}
        )
        
        if confidence is not None:
            await self.record_histogram(
                f"speech_{operation}_confidence",
                MetricCategory.SPEECH,
                confidence,
                tags={"language": language}
            )
    
    async def track_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float
    ):
        """Track API request metrics."""
        await self.increment_counter(
            "api_requests_total",
            MetricCategory.API,
            tags={
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code)
            }
        )
        
        await self.record_timer(
            "api_request_duration_seconds",
            MetricCategory.API,
            duration,
            tags={
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code)
            }
        )
        
        # Track error rates
        if status_code >= 400:
            await self.increment_counter(
                "api_errors_total",
                MetricCategory.API,
                tags={
                    "endpoint": endpoint,
                    "status_code": str(status_code)
                }
            )
    
    async def track_system_resource(
        self,
        resource_type: str,  # "cpu", "memory", "disk"
        usage_percent: float,
        host: Optional[str] = None
    ):
        """Track system resource usage."""
        await self.set_gauge(
            f"system_{resource_type}_usage_percent",
            MetricCategory.SYSTEM,
            usage_percent,
            tags={"host": host or "unknown"}
        )
    
    async def track_database_operation(
        self,
        operation: str,  # "read", "write", "update", "delete"
        collection: str,
        duration: float,
        success: bool
    ):
        """Track database operation metrics."""
        status = "success" if success else "failure"
        
        await self.increment_counter(
            "database_operations_total",
            MetricCategory.SYSTEM,
            tags={
                "operation": operation,
                "collection": collection,
                "status": status
            }
        )
        
        await self.record_timer(
            "database_operation_duration_seconds",
            MetricCategory.SYSTEM,
            duration,
            tags={
                "operation": operation,
                "collection": collection
            }
        )
    
    # Query methods
    async def get_counter_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        key = self._get_metric_key(name, tags or {})
        return self._counters.get(key, 0)
    
    async def get_gauge_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value."""
        key = self._get_metric_key(name, tags or {})
        return self._gauges.get(key)
    
    async def get_histogram_stats(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, float]]:
        """Get histogram statistics."""
        key = self._get_metric_key(name, tags or {})
        values = self._histograms.get(key, [])
        
        if not values:
            return None
        
        values_sorted = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "p50": values_sorted[int(count * 0.5)],
            "p90": values_sorted[int(count * 0.9)],
            "p95": values_sorted[int(count * 0.95)],
            "p99": values_sorted[int(count * 0.99)]
        }
    
    async def get_metrics_summary(
        self,
        category: Optional[MetricCategory] = None,
        time_range: Optional[int] = None  # minutes
    ) -> Dict[str, Any]:
        """Get summary of metrics."""
        try:
            query = {}
            
            if category:
                query["category"] = category.value
            
            if time_range:
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_range)
                query["timestamp"] = {"$gte": cutoff_time}
            
            # Get recent metrics from database
            cursor = self.metrics_collection.find(query).sort("timestamp", -1).limit(1000)
            metrics = await cursor.to_list(length=1000)
            
            # Aggregate by metric name
            summary = {}
            
            for metric_doc in metrics:
                name = metric_doc["name"]
                metric_type = metric_doc["type"]
                value = metric_doc["value"]
                
                if name not in summary:
                    summary[name] = {
                        "type": metric_type,
                        "values": [],
                        "count": 0,
                        "latest_value": value,
                        "latest_timestamp": metric_doc["timestamp"]
                    }
                
                summary[name]["values"].append(value)
                summary[name]["count"] += 1
                
                # Update latest if this is more recent
                if metric_doc["timestamp"] > summary[name]["latest_timestamp"]:
                    summary[name]["latest_value"] = value
                    summary[name]["latest_timestamp"] = metric_doc["timestamp"]
            
            # Calculate statistics for each metric
            for name, data in summary.items():
                values = data["values"]
                if values:
                    data["min"] = min(values)
                    data["max"] = max(values)
                    data["mean"] = sum(values) / len(values)
                    
                    if data["type"] == "counter":
                        data["total"] = sum(values)
                    elif data["type"] == "gauge":
                        data["current"] = data["latest_value"]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    async def get_business_kpis(
        self,
        time_range: Optional[int] = None  # minutes
    ) -> Dict[str, Any]:
        """Get key business performance indicators."""
        try:
            query = {"category": MetricCategory.BUSINESS.value}
            
            if time_range:
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_range)
                query["timestamp"] = {"$gte": cutoff_time}
            
            # Aggregate business metrics
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "name": "$name",
                            "tags": "$tags"
                        },
                        "total_value": {"$sum": "$value"},
                        "count": {"$sum": 1},
                        "avg_value": {"$avg": "$value"},
                        "latest_timestamp": {"$max": "$timestamp"}
                    }
                }
            ]
            
            results = await self.metrics_collection.aggregate(pipeline).to_list(length=None)
            
            # Process results into KPIs
            kpis = {
                "call_volume": {"total": 0, "inbound": 0, "outbound": 0},
                "completion_rate": 0.0,
                "qualification_rate": 0.0,
                "handoff_rate": 0.0,
                "avg_call_duration": 0.0,
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "language_usage": {}
            }
            
            calls_total = 0
            calls_completed = 0
            calls_qualified = 0
            handoffs_total = 0
            
            for result in results:
                name = result["_id"]["name"]
                tags = result["_id"]["tags"]
                total_value = result["total_value"]
                
                if name == "calls_total":
                    calls_total += total_value
                    direction = tags.get("direction", "unknown")
                    if direction in ["inbound", "outbound"]:
                        kpis["call_volume"][direction] += total_value
                    kpis["call_volume"]["total"] += total_value
                
                elif name == "calls_completed_total":
                    calls_completed += total_value
                
                elif name == "calls_qualified_total":
                    calls_qualified += total_value
                
                elif name == "handoffs_total":
                    handoffs_total += total_value
                
                elif name == "sentiment_distribution":
                    category = tags.get("category", "neutral")
                    if category in kpis["sentiment_distribution"]:
                        kpis["sentiment_distribution"][category] += total_value
                
                elif name.endswith("_total") and "language" in tags:
                    language = tags["language"]
                    if language not in kpis["language_usage"]:
                        kpis["language_usage"][language] = 0
                    kpis["language_usage"][language] += total_value
            
            # Calculate rates
            if calls_total > 0:
                kpis["completion_rate"] = calls_completed / calls_total
                kpis["qualification_rate"] = calls_qualified / calls_total
                kpis["handoff_rate"] = handoffs_total / calls_total
            
            # Get average call duration
            duration_stats = await self.get_histogram_stats("call_duration_seconds")
            if duration_stats:
                kpis["avg_call_duration"] = duration_stats["mean"]
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error getting business KPIs: {e}")
            return {}
    
    # Private methods
    def _get_metric_key(self, name: str, tags: Dict[str, str]) -> str:
        """Generate a unique key for a metric with tags."""
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}#{tag_str}" if tag_str else name
    
    async def _store_metric(self, metric: Metric):
        """Store a metric in the database."""
        try:
            await self.metrics_collection.insert_one(metric.model_dump())
        except Exception as e:
            logger.error(f"Error storing metric: {e}")
    
    async def _periodic_aggregation(self):
        """Periodic task to aggregate metrics."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._aggregate_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic aggregation: {e}")
                await asyncio.sleep(60)
    
    async def _aggregate_metrics(self):
        """Aggregate metrics for efficient querying."""
        try:
            now = datetime.now(timezone.utc)
            
            # Aggregate metrics from the last hour
            start_time = now.replace(minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            # Check if already aggregated
            existing = await self.aggregated_metrics_collection.find_one({
                "period_start": start_time,
                "period_end": end_time
            })
            
            if existing:
                return  # Already aggregated
            
            # Aggregate metrics
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_time, "$lt": end_time}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "name": "$name",
                            "type": "$type",
                            "category": "$category",
                            "tags": "$tags"
                        },
                        "count": {"$sum": 1},
                        "sum": {"$sum": "$value"},
                        "avg": {"$avg": "$value"},
                        "min": {"$min": "$value"},
                        "max": {"$max": "$value"}
                    }
                }
            ]
            
            results = await self.metrics_collection.aggregate(pipeline).to_list(length=None)
            
            # Store aggregated results
            for result in results:
                aggregated_metric = {
                    "name": result["_id"]["name"],
                    "type": result["_id"]["type"],
                    "category": result["_id"]["category"],
                    "tags": result["_id"]["tags"],
                    "period_start": start_time,
                    "period_end": end_time,
                    "count": result["count"],
                    "sum": result["sum"],
                    "avg": result["avg"],
                    "min": result["min"],
                    "max": result["max"],
                    "created_at": now
                }
                
                await self.aggregated_metrics_collection.insert_one(aggregated_metric)
            
            logger.info(f"Aggregated {len(results)} metrics for period {start_time} - {end_time}")
            
        except Exception as e:
            logger.error(f"Error aggregating metrics: {e}")


# Context manager for timing operations
class MetricTimer:
    """Context manager for timing operations."""
    
    def __init__(
        self,
        collector: MetricsCollector,
        name: str,
        category: MetricCategory,
        tags: Optional[Dict[str, str]] = None
    ):
        self.collector = collector
        self.name = name
        self.category = category
        self.tags = tags or {}
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            await self.collector.record_timer(
                self.name,
                self.category,
                duration,
                self.tags
            )


# Dependency injection
_metrics_collector: Optional[MetricsCollector] = None


async def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        from app.database import get_database
        
        database = await get_database()
        _metrics_collector = MetricsCollector(database)
        await _metrics_collector.start()
    
    return _metrics_collector


async def shutdown_metrics_collector():
    """Shutdown metrics collector."""
    global _metrics_collector
    if _metrics_collector:
        await _metrics_collector.stop()
        _metrics_collector = None
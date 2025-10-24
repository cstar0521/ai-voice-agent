"""
Metrics collection and aggregation service.
Tracks system performance and business KPIs.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.metrics import CallMetrics, DailyMetrics, SystemMetrics
from app.logging_config import get_logger

logger = get_logger('business')


class MetricsService:
    """Service for collecting and aggregating metrics."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.call_metrics_collection = db["call_metrics"]
        self.daily_metrics_collection = db["daily_metrics"]
        self.system_metrics_collection = db["system_metrics"]
    
    async def record_call_metrics(self, metrics: CallMetrics) -> None:
        """
        Record metrics for a completed call.
        
        Args:
            metrics: CallMetrics object
        """
        try:
            await self.call_metrics_collection.insert_one(metrics.model_dump())
            logger.info(
                f"Recorded call metrics",
                extra={
                    "call_id": metrics.call_id,
                    "duration": metrics.duration_seconds,
                    "status": metrics.status
                }
            )
        except Exception as e:
            logger.error(f"Failed to record call metrics: {e}", exc_info=True)
    
    async def aggregate_daily_metrics(self, date: str) -> DailyMetrics:
        """
        Aggregate metrics for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            DailyMetrics object
        """
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d")
        next_date = target_date + timedelta(days=1)
        
        # Query call metrics for the date
        pipeline = [
            {
                "$match": {
                    "start_time": {
                        "$gte": target_date,
                        "$lt": next_date
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_calls": {"$sum": 1},
                    "inbound_calls": {
                        "$sum": {"$cond": [{"$eq": ["$direction", "inbound"]}, 1, 0]}
                    },
                    "outbound_calls": {
                        "$sum": {"$cond": [{"$eq": ["$direction", "outbound"]}, 1, 0]}
                    },
                    "completed_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "failed_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                    },
                    "no_answer_calls": {
                        "$sum": {"$cond": [{"$eq": ["$status", "no_answer"]}, 1, 0]}
                    },
                    "avg_duration": {"$avg": "$duration_seconds"},
                    "avg_asr_latency": {"$avg": "$asr_latency_ms"},
                    "avg_tts_latency": {"$avg": "$tts_latency_ms"},
                    "qualified_calls": {
                        "$sum": {"$cond": ["$qualification_completed", 1, 0]}
                    },
                    "handoff_calls": {
                        "$sum": {"$cond": ["$handoff_triggered", 1, 0]}
                    },
                    "avg_sentiment": {"$avg": "$sentiment_score"},
                    "positive_sentiment": {
                        "$sum": {"$cond": [{"$gte": ["$sentiment_score", 0.3]}, 1, 0]}
                    },
                    "neutral_sentiment": {
                        "$sum": {"$cond": [
                            {"$and": [
                                {"$gt": ["$sentiment_score", -0.3]},
                                {"$lt": ["$sentiment_score", 0.3]}
                            ]},
                            1, 0
                        ]}
                    },
                    "negative_sentiment": {
                        "$sum": {"$cond": [{"$lte": ["$sentiment_score", -0.3]}, 1, 0]}
                    },
                    "total_errors": {"$sum": "$error_count"}
                }
            }
        ]
        
        result = await self.call_metrics_collection.aggregate(pipeline).to_list(1)
        
        if not result:
            return DailyMetrics(date=date)
        
        data = result[0]
        total_calls = data.get("total_calls", 0)
        qualified_calls = data.get("qualified_calls", 0)
        
        # Calculate rates
        qualification_rate = (qualified_calls / total_calls * 100) if total_calls > 0 else 0
        handoff_rate = (data.get("handoff_calls", 0) / qualified_calls * 100) if qualified_calls > 0 else 0
        error_rate = (data.get("total_errors", 0) / total_calls) if total_calls > 0 else 0
        
        # Get language distribution
        language_pipeline = [
            {
                "$match": {
                    "start_time": {
                        "$gte": target_date,
                        "$lt": next_date
                    }
                }
            },
            {
                "$group": {
                    "_id": "$language",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        language_results = await self.call_metrics_collection.aggregate(language_pipeline).to_list(None)
        language_distribution = {item["_id"]: item["count"] for item in language_results}
        
        # Create DailyMetrics object
        daily_metrics = DailyMetrics(
            date=date,
            total_calls=total_calls,
            inbound_calls=data.get("inbound_calls", 0),
            outbound_calls=data.get("outbound_calls", 0),
            completed_calls=data.get("completed_calls", 0),
            failed_calls=data.get("failed_calls", 0),
            no_answer_calls=data.get("no_answer_calls", 0),
            avg_call_duration_seconds=data.get("avg_duration", 0.0) or 0.0,
            avg_asr_latency_ms=data.get("avg_asr_latency", 0.0) or 0.0,
            avg_tts_latency_ms=data.get("avg_tts_latency", 0.0) or 0.0,
            qualification_rate=qualification_rate,
            handoff_rate=handoff_rate,
            avg_sentiment_score=data.get("avg_sentiment", 0.0) or 0.0,
            positive_sentiment_count=data.get("positive_sentiment", 0),
            neutral_sentiment_count=data.get("neutral_sentiment", 0),
            negative_sentiment_count=data.get("negative_sentiment", 0),
            language_distribution=language_distribution,
            total_errors=data.get("total_errors", 0),
            error_rate=error_rate
        )
        
        # Store aggregated metrics
        await self.daily_metrics_collection.update_one(
            {"date": date},
            {"$set": daily_metrics.model_dump()},
            upsert=True
        )
        
        logger.info(f"Aggregated daily metrics for {date}", extra={"total_calls": total_calls})
        
        return daily_metrics
    
    async def get_daily_metrics(self, date: str) -> Optional[DailyMetrics]:
        """
        Get aggregated daily metrics for a specific date.
        
        Args:
            date: Date string in YYYY-MM-D format
            
        Returns:
            DailyMetrics object or None if not found
        """
        data = await self.daily_metrics_collection.find_one({"date": date})
        if data:
            data.pop("_id", None)
            return DailyMetrics(**data)
        return None
    
    async def get_metrics_range(self, start_date: str, end_date: str) -> List[DailyMetrics]:
        """
        Get daily metrics for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of DailyMetrics objects
        """
        cursor = self.daily_metrics_collection.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", 1)
        
        metrics = []
        async for data in cursor:
            data.pop("_id", None)
            metrics.append(DailyMetrics(**data))
        
        return metrics
    
    async def record_system_metrics(self, metrics: SystemMetrics) -> None:
        """
        Record real-time system metrics.
        
        Args:
            metrics: SystemMetrics object
        """
        try:
            await self.system_metrics_collection.insert_one(metrics.model_dump())
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}", exc_info=True)
    
    async def get_current_metrics(self) -> Dict:
        """
        Get current system metrics summary.
        
        Returns:
            Dictionary with current metrics
        """
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get or aggregate today's metrics
        daily_metrics = await self.get_daily_metrics(today)
        if not daily_metrics:
            daily_metrics = await self.aggregate_daily_metrics(today)
        
        # Get active calls count
        from app.repositories.call_repository import CallRepository
        call_repo = CallRepository(self.db)
        active_calls = await call_repo.collection.count_documents({
            "status": {"$in": ["initiated", "connected", "in_progress"]}
        })
        
        return {
            "total_calls": daily_metrics.total_calls,
            "active_calls": active_calls,
            "call_completion_rate": daily_metrics.qualification_rate / 100,
            "handoff_rate": daily_metrics.handoff_rate / 100,
            "avg_qualification_time": daily_metrics.avg_call_duration_seconds,
            "sentiment_distribution": {
                "positive": daily_metrics.positive_sentiment_count,
                "neutral": daily_metrics.neutral_sentiment_count,
                "negative": daily_metrics.negative_sentiment_count
            },
            "language_usage": daily_metrics.language_distribution
        }
    
    async def check_alert_thresholds(self) -> List[Dict]:
        """
        Check if any metrics exceed alert thresholds.
        
        Returns:
            List of alerts
        """
        alerts = []
        today = datetime.now().strftime("%Y-%m-%d")
        daily_metrics = await self.get_daily_metrics(today)
        
        if not daily_metrics:
            return alerts
        
        # Check error rate (>5%)
        if daily_metrics.error_rate > 0.05:
            alerts.append({
                "type": "error_rate",
                "severity": "critical",
                "message": f"High error rate: {daily_metrics.error_rate:.2%}",
                "current_value": daily_metrics.error_rate,
                "threshold": 0.05
            })
        
        # Check call failure rate (>10%)
        failure_rate = (daily_metrics.failed_calls / daily_metrics.total_calls) if daily_metrics.total_calls > 0 else 0
        if failure_rate > 0.10:
            alerts.append({
                "type": "call_failure_rate",
                "severity": "critical",
                "message": f"High call failure rate: {failure_rate:.2%}",
                "current_value": failure_rate,
                "threshold": 0.10
            })
        
        # Check API latency (>2000ms)
        if daily_metrics.avg_asr_latency_ms > 2000:
            alerts.append({
                "type": "asr_latency",
                "severity": "warning",
                "message": f"High ASR latency: {daily_metrics.avg_asr_latency_ms:.0f}ms",
                "current_value": daily_metrics.avg_asr_latency_ms,
                "threshold": 2000
            })
        
        return alerts

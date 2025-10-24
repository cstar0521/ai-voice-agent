"""
Alerting system for monitoring system health and performance.
Sends alerts via email, Slack, and other channels when thresholds are exceeded.
"""

import asyncio
import logging
import smtplib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp
import json

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.services.metrics_collector import MetricsCollector, MetricCategory
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class AlertRule(BaseModel):
    """Model for alert rule configuration."""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    evaluation_window: int = 300  # seconds
    cooldown_period: int = 900  # seconds
    tags: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    """Model for an active alert."""
    alert_id: str
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    metric_name: str
    current_value: float
    threshold: float
    condition: str
    tags: Dict[str, str] = Field(default_factory=dict)
    fired_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notification_sent: bool = False


class AlertingSystem:
    """Main alerting system class."""
    
    def __init__(self, database: AsyncIOMotorDatabase, metrics_collector: MetricsCollector):
        self.db = database
        self.metrics_collector = metrics_collector
        self.rules_collection = database.alert_rules
        self.alerts_collection = database.alerts
        
        # Built-in alert rules
        self.default_rules = self._get_default_rules()
        
        # Alert evaluation task
        self._evaluation_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Notification channels
        self.notification_channels = []
    
    async def start(self):
        """Start the alerting system."""
        self._running = True
        
        # Initialize default rules
        await self._initialize_default_rules()
        
        # Start evaluation task
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        
        logger.info("Alerting system started")
    
    async def stop(self):
        """Stop the alerting system."""
        self._running = False
        
        if self._evaluation_task:
            self._evaluation_task.cancel()
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Alerting system stopped")
    
    async def add_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule."""
        try:
            await self.rules_collection.insert_one(rule.model_dump())
            logger.info(f"Added alert rule: {rule.rule_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding alert rule: {e}")
            return False
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule."""
        try:
            result = await self.rules_collection.update_one(
                {"rule_id": rule_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating alert rule: {e}")
            return False
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        try:
            result = await self.rules_collection.delete_one({"rule_id": rule_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting alert rule: {e}")
            return False
    
    async def get_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        try:
            cursor = self.rules_collection.find({})
            rules_docs = await cursor.to_list(length=None)
            return [AlertRule(**doc) for doc in rules_docs]
        except Exception as e:
            logger.error(f"Error getting alert rules: {e}")
            return []
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        try:
            cursor = self.alerts_collection.find({"status": AlertStatus.ACTIVE.value})
            alerts_docs = await cursor.to_list(length=None)
            return [Alert(**doc) for doc in alerts_docs]
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        try:
            result = await self.alerts_collection.update_one(
                {"alert_id": alert_id},
                {
                    "$set": {
                        "status": AlertStatus.ACKNOWLEDGED.value,
                        "acknowledged_at": datetime.now(timezone.utc),
                        "acknowledged_by": acknowledged_by
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        try:
            result = await self.alerts_collection.update_one(
                {"alert_id": alert_id},
                {
                    "$set": {
                        "status": AlertStatus.RESOLVED.value,
                        "resolved_at": datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    async def _evaluation_loop(self):
        """Main evaluation loop for checking alert conditions."""
        while self._running:
            try:
                await self._evaluate_rules()
                await asyncio.sleep(60)  # Evaluate every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(60)
    
    async def _evaluate_rules(self):
        """Evaluate all alert rules."""
        try:
            rules = await self.get_rules()
            
            for rule in rules:
                if not rule.enabled:
                    continue
                
                try:
                    await self._evaluate_rule(rule)
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in rule evaluation: {e}")
    
    async def _evaluate_rule(self, rule: AlertRule):
        """Evaluate a single alert rule."""
        try:
            # Get current metric value
            current_value = await self._get_metric_value(rule.metric_name, rule.tags)
            
            if current_value is None:
                return  # Metric not available
            
            # Check condition
            condition_met = self._check_condition(
                current_value, rule.condition, rule.threshold
            )
            
            # Check if alert already exists
            existing_alert = await self.alerts_collection.find_one({
                "rule_id": rule.rule_id,
                "status": {"$in": [AlertStatus.ACTIVE.value, AlertStatus.ACKNOWLEDGED.value]}
            })
            
            if condition_met and not existing_alert:
                # Fire new alert
                await self._fire_alert(rule, current_value)
            
            elif not condition_met and existing_alert:
                # Resolve existing alert
                await self.resolve_alert(existing_alert["alert_id"])
                logger.info(f"Auto-resolved alert: {existing_alert['alert_id']}")
        
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
    
    async def _get_metric_value(self, metric_name: str, tags: Dict[str, str]) -> Optional[float]:
        """Get current value of a metric."""
        try:
            # For counters, get the rate over the last 5 minutes
            if metric_name.endswith("_total") or metric_name.endswith("_count"):
                return await self._get_metric_rate(metric_name, tags, 300)  # 5 minutes
            
            # For gauges, get the latest value
            elif "usage" in metric_name or "percent" in metric_name:
                return await self.metrics_collector.get_gauge_value(metric_name, tags)
            
            # For histograms/timers, get the 95th percentile
            elif "duration" in metric_name or "latency" in metric_name:
                stats = await self.metrics_collector.get_histogram_stats(metric_name, tags)
                return stats["p95"] if stats else None
            
            # Default to gauge value
            else:
                return await self.metrics_collector.get_gauge_value(metric_name, tags)
        
        except Exception as e:
            logger.error(f"Error getting metric value for {metric_name}: {e}")
            return None
    
    async def _get_metric_rate(self, metric_name: str, tags: Dict[str, str], window_seconds: int) -> Optional[float]:
        """Calculate rate of change for a counter metric."""
        try:
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(seconds=window_seconds)
            
            # Query metrics from database
            query = {
                "name": metric_name,
                "timestamp": {"$gte": start_time, "$lte": now}
            }
            
            # Add tag filters
            for key, value in tags.items():
                query[f"tags.{key}"] = value
            
            cursor = self.metrics_collector.metrics_collection.find(query).sort("timestamp", 1)
            metrics = await cursor.to_list(length=None)
            
            if len(metrics) < 2:
                return None
            
            # Calculate rate (events per second)
            first_metric = metrics[0]
            last_metric = metrics[-1]
            
            value_diff = last_metric["value"] - first_metric["value"]
            time_diff = (last_metric["timestamp"] - first_metric["timestamp"]).total_seconds()
            
            if time_diff > 0:
                return value_diff / time_diff
            
            return None
        
        except Exception as e:
            logger.error(f"Error calculating metric rate: {e}")
            return None
    
    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Check if alert condition is met."""
        if condition == "gt":
            return value > threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "lte":
            return value <= threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.001  # Float equality with tolerance
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False
    
    async def _fire_alert(self, rule: AlertRule, current_value: float):
        """Fire a new alert."""
        try:
            alert_id = f"alert_{rule.rule_id}_{int(datetime.now().timestamp())}"
            
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                severity=rule.severity,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold=rule.threshold,
                condition=rule.condition,
                tags=rule.tags
            )
            
            # Store alert
            await self.alerts_collection.insert_one(alert.model_dump())
            
            # Send notifications
            await self._send_notifications(alert)
            
            logger.warning(f"Alert fired: {alert.name} - {current_value} {rule.condition} {rule.threshold}")
        
        except Exception as e:
            logger.error(f"Error firing alert: {e}")
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels."""
        try:
            # Email notification
            if settings.smtp_username and settings.alert_email_to:
                await self._send_email_notification(alert)
            
            # Slack notification
            if settings.slack_webhook_url:
                await self._send_slack_notification(alert)
            
            # Mark notification as sent
            await self.alerts_collection.update_one(
                {"alert_id": alert.alert_id},
                {"$set": {"notification_sent": True}}
            )
        
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification."""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = settings.alert_email_from
            msg['To'] = settings.alert_email_to
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.name}"
            
            # Email body
            body = f"""
Alert: {alert.name}
Severity: {alert.severity.value.upper()}
Description: {alert.description}

Metric: {alert.metric_name}
Current Value: {alert.current_value}
Threshold: {alert.threshold}
Condition: {alert.condition}

Fired At: {alert.fired_at.isoformat()}
Alert ID: {alert.alert_id}

Tags: {json.dumps(alert.tags, indent=2)}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for alert: {alert.alert_id}")
        
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification."""
        try:
            # Determine color based on severity
            color_map = {
                AlertSeverity.LOW: "#36a64f",      # Green
                AlertSeverity.MEDIUM: "#ff9500",   # Orange
                AlertSeverity.HIGH: "#ff0000",     # Red
                AlertSeverity.CRITICAL: "#8B0000"  # Dark Red
            }
            
            color = color_map.get(alert.severity, "#ff0000")
            
            # Create Slack message
            payload = {
                "text": f"Alert: {alert.name}",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Metric",
                                "value": alert.metric_name,
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert.current_value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"{alert.condition} {alert.threshold}",
                                "short": True
                            },
                            {
                                "title": "Description",
                                "value": alert.description,
                                "short": False
                            }
                        ],
                        "footer": f"Alert ID: {alert.alert_id}",
                        "ts": int(alert.fired_at.timestamp())
                    }
                ]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.slack_webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert: {alert.alert_id}")
                    else:
                        logger.error(f"Failed to send Slack notification: {response.status}")
        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def _get_default_rules(self) -> List[AlertRule]:
        """Get default alert rules."""
        return [
            # High error rate
            AlertRule(
                rule_id="high_error_rate",
                name="High API Error Rate",
                description="API error rate is above 5%",
                metric_name="api_errors_total",
                condition="gt",
                threshold=0.05,  # 5% error rate
                severity=AlertSeverity.HIGH,
                evaluation_window=300,
                cooldown_period=900
            ),
            
            # High API latency
            AlertRule(
                rule_id="high_api_latency",
                name="High API Latency",
                description="API response time is above 2 seconds",
                metric_name="api_request_duration_seconds",
                condition="gt",
                threshold=2.0,
                severity=AlertSeverity.MEDIUM,
                evaluation_window=300,
                cooldown_period=600
            ),
            
            # High call failure rate
            AlertRule(
                rule_id="high_call_failure_rate",
                name="High Call Failure Rate",
                description="Call failure rate is above 10%",
                metric_name="calls_failed_total",
                condition="gt",
                threshold=0.1,  # 10% failure rate
                severity=AlertSeverity.HIGH,
                evaluation_window=300,
                cooldown_period=900
            ),
            
            # Low ASR accuracy
            AlertRule(
                rule_id="low_asr_accuracy",
                name="Low ASR Accuracy",
                description="Speech recognition accuracy is below 80%",
                metric_name="speech_asr_confidence",
                condition="lt",
                threshold=0.8,
                severity=AlertSeverity.MEDIUM,
                evaluation_window=600,
                cooldown_period=1800
            ),
            
            # High CPU usage
            AlertRule(
                rule_id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage is above 80%",
                metric_name="system_cpu_usage_percent",
                condition="gt",
                threshold=80.0,
                severity=AlertSeverity.MEDIUM,
                evaluation_window=300,
                cooldown_period=600
            ),
            
            # High memory usage
            AlertRule(
                rule_id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage is above 85%",
                metric_name="system_memory_usage_percent",
                condition="gt",
                threshold=85.0,
                severity=AlertSeverity.HIGH,
                evaluation_window=300,
                cooldown_period=600
            ),
            
            # Database connection issues
            AlertRule(
                rule_id="database_errors",
                name="Database Connection Errors",
                description="High rate of database connection errors",
                metric_name="database_operations_total",
                condition="gt",
                threshold=0.05,  # 5% error rate
                severity=AlertSeverity.CRITICAL,
                evaluation_window=180,
                cooldown_period=300,
                tags={"status": "failure"}
            )
        ]
    
    async def _initialize_default_rules(self):
        """Initialize default alert rules if they don't exist."""
        try:
            for rule in self.default_rules:
                existing = await self.rules_collection.find_one({"rule_id": rule.rule_id})
                if not existing:
                    await self.rules_collection.insert_one(rule.model_dump())
                    logger.info(f"Initialized default alert rule: {rule.rule_id}")
        
        except Exception as e:
            logger.error(f"Error initializing default rules: {e}")


# Dependency injection
_alerting_system: Optional[AlertingSystem] = None


async def get_alerting_system() -> AlertingSystem:
    """Get alerting system instance."""
    global _alerting_system
    if _alerting_system is None:
        from app.database import get_database
        from app.services.metrics_collector import get_metrics_collector
        
        database = await get_database()
        metrics_collector = await get_metrics_collector()
        _alerting_system = AlertingSystem(database, metrics_collector)
        await _alerting_system.start()
    
    return _alerting_system


async def shutdown_alerting_system():
    """Shutdown alerting system."""
    global _alerting_system
    if _alerting_system:
        await _alerting_system.stop()
        _alerting_system = None
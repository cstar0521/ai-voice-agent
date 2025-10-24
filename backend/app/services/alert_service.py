"""
Alerting service for sending notifications about system issues.
Supports email and Slack notifications.
"""

import logging
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from datetime import datetime

from config import settings
from app.logging_config import get_logger
from app.models.metrics import AlertMetrics

logger = get_logger('business')


class AlertService:
    """Service for sending alerts via email and Slack."""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'smtp_server', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_username = getattr(settings, 'smtp_username', None)
        self.smtp_password = getattr(settings, 'smtp_password', None)
        self.alert_email_from = getattr(settings, 'alert_email_from', 'alerts@voiceagent.com')
        self.alert_email_to = getattr(settings, 'alert_email_to', '').split(',')
        
        self.slack_webhook_url = getattr(settings, 'slack_webhook_url', None)
        
        self.email_enabled = bool(self.smtp_username and self.smtp_password)
        self.slack_enabled = bool(self.slack_webhook_url)
    
    async def send_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float,
        threshold_value: float,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Send an alert via configured channels.
        
        Args:
            alert_type: Type of alert (error_rate, api_latency, call_failure_rate)
            severity: Severity level (warning, critical)
            message: Alert message
            current_value: Current metric value
            threshold_value: Threshold that was exceeded
            metadata: Additional context
        """
        alert = AlertMetrics(
            timestamp=datetime.utcnow(),
            metric_type=alert_type,
            current_value=current_value,
            threshold_value=threshold_value,
            severity=severity,
            message=message,
            metadata=metadata or {}
        )
        
        logger.warning(
            f"Alert triggered: {message}",
            extra={
                "alert_type": alert_type,
                "severity": severity,
                "current_value": current_value,
                "threshold": threshold_value
            }
        )
        
        # Send via email
        if self.email_enabled:
            await self._send_email_alert(alert)
        
        # Send via Slack
        if self.slack_enabled:
            await self._send_slack_alert(alert)
    
    async def _send_email_alert(self, alert: AlertMetrics) -> None:
        """Send alert via email."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.severity.upper()}] AI Voice Agent Alert: {alert.metric_type}"
            msg['From'] = self.alert_email_from
            msg['To'] = ', '.join(self.alert_email_to)
            
            # Create HTML body
            html = f"""
            <html>
              <body>
                <h2 style="color: {'#dc3545' if alert.severity == 'critical' else '#ffc107'};">
                  {alert.severity.upper()} Alert
                </h2>
                <p><strong>Alert Type:</strong> {alert.metric_type}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Current Value:</strong> {alert.current_value:.2f}</p>
                <p><strong>Threshold:</strong> {alert.threshold_value:.2f}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                {self._format_metadata_html(alert.metadata)}
                
                <hr>
                <p style="color: #666; font-size: 12px;">
                  This is an automated alert from the AI Voice Loan Agent system.
                </p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {len(self.alert_email_to)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)
    
    async def _send_slack_alert(self, alert: AlertMetrics) -> None:
        """Send alert via Slack webhook."""
        try:
            # Determine color based on severity
            color = "#dc3545" if alert.severity == "critical" else "#ffc107"
            
            # Create Slack message
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"{alert.severity.upper()} Alert: {alert.metric_type}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Current Value",
                                "value": f"{alert.current_value:.2f}",
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"{alert.threshold_value:.2f}",
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": False
                            }
                        ],
                        "footer": "AI Voice Loan Agent",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            # Add metadata fields
            if alert.metadata:
                for key, value in alert.metadata.items():
                    payload["attachments"][0]["fields"].append({
                        "title": key.replace('_', ' ').title(),
                        "value": str(value),
                        "short": True
                    })
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
            
            logger.info("Slack alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}", exc_info=True)
    
    def _format_metadata_html(self, metadata: Dict) -> str:
        """Format metadata as HTML."""
        if not metadata:
            return ""
        
        html = "<h3>Additional Details:</h3><ul>"
        for key, value in metadata.items():
            html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        html += "</ul>"
        return html
    
    async def send_error_rate_alert(self, error_rate: float, total_calls: int) -> None:
        """Send alert for high error rate."""
        await self.send_alert(
            alert_type="error_rate",
            severity="critical",
            message=f"Error rate has exceeded threshold: {error_rate:.2%}",
            current_value=error_rate,
            threshold_value=0.05,
            metadata={
                "total_calls": total_calls,
                "action_required": "Check logs for error patterns"
            }
        )
    
    async def send_latency_alert(
        self,
        service: str,
        latency_ms: float
    ) -> None:
        """Send alert for high API latency."""
        await self.send_alert(
            alert_type="api_latency",
            severity="warning",
            message=f"{service} latency has exceeded threshold: {latency_ms:.0f}ms",
            current_value=latency_ms,
            threshold_value=2000.0,
            metadata={
                "service": service,
                "action_required": "Check service health and network connectivity"
            }
        )
    
    async def send_call_failure_alert(
        self,
        failure_rate: float,
        failed_calls: int,
        total_calls: int
    ) -> None:
        """Send alert for high call failure rate."""
        await self.send_alert(
            alert_type="call_failure_rate",
            severity="critical",
            message=f"Call failure rate has exceeded threshold: {failure_rate:.2%}",
            current_value=failure_rate,
            threshold_value=0.10,
            metadata={
                "failed_calls": failed_calls,
                "total_calls": total_calls,
                "action_required": "Check telephony service and call logs"
            }
        )
    
    async def send_test_alert(self) -> Dict[str, bool]:
        """
        Send a test alert to verify configuration.
        
        Returns:
            Dictionary with status of each channel
        """
        test_alert = AlertMetrics(
            timestamp=datetime.utcnow(),
            metric_type="test",
            current_value=0.0,
            threshold_value=0.0,
            severity="warning",
            message="This is a test alert to verify alerting configuration",
            metadata={"test": True}
        )
        
        results = {
            "email": False,
            "slack": False
        }
        
        if self.email_enabled:
            try:
                await self._send_email_alert(test_alert)
                results["email"] = True
            except Exception as e:
                logger.error(f"Test email failed: {e}")
        
        if self.slack_enabled:
            try:
                await self._send_slack_alert(test_alert)
                results["slack"] = True
            except Exception as e:
                logger.error(f"Test Slack alert failed: {e}")
        
        return results


# Background task to check metrics and send alerts
async def check_and_send_alerts(db) -> None:
    """
    Background task to check metrics and send alerts.
    Should be run periodically (e.g., every 5 minutes).
    """
    from app.services.metrics_service import MetricsService
    
    metrics_service = MetricsService(db)
    alert_service = AlertService()
    
    # Check for alerts
    alerts = await metrics_service.check_alert_thresholds()
    
    for alert in alerts:
        if alert["type"] == "error_rate":
            await alert_service.send_error_rate_alert(
                error_rate=alert["current_value"],
                total_calls=alert.get("total_calls", 0)
            )
        elif alert["type"] == "call_failure_rate":
            await alert_service.send_call_failure_alert(
                failure_rate=alert["current_value"],
                failed_calls=alert.get("failed_calls", 0),
                total_calls=alert.get("total_calls", 0)
            )
        elif alert["type"] == "asr_latency":
            await alert_service.send_latency_alert(
                service="ASR",
                latency_ms=alert["current_value"]
            )

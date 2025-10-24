# Logging and Monitoring System

Comprehensive logging, metrics collection, and alerting system for the AI Voice Loan Agent.

## Overview

The system provides:
- **Structured JSON logging** with contextual information
- **Metrics collection** for performance and business KPIs
- **Automated alerting** via email and Slack
- **Real-time monitoring** dashboards

## Structured Logging

### Features

- JSON-formatted logs for easy parsing
- Contextual tracking (call_id, lead_id)
- Component-based logging (API, telephony, speech, business, database, security)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Configuration

Set environment variables:

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=/var/log/voice-agent.log  # Optional file output
```

### Usage

```python
from app.logging_config import get_logger, set_call_context, log_api_request

# Get component logger
logger = get_logger('api')

# Set call context for automatic inclusion in logs
set_call_context(call_id='call_123', lead_id='lead_456')

# Log API request
log_api_request(logger, 'POST', '/api/v1/calls', 201, 145.3, user_id='user_123')

# Log with structured data
logger.info("Call completed", extra={
    "duration": 180,
    "status": "completed",
    "qualification": "public_secured"
})
```

### Log Format

```json
{
  "timestamp": "2024-10-24T10:30:45.123Z",
  "level": "INFO",
  "component": "api",
  "message": "Call completed",
  "call_id": "call_123",
  "lead_id": "lead_456",
  "duration": 180,
  "status": "completed",
  "source": {
    "file": "/app/services/call_service.py",
    "line": 145,
    "function": "complete_call"
  }
}
```

## Metrics Collection

### Tracked Metrics

**Call Metrics:**
- Call volume (total, inbound, outbound)
- Call outcomes (completed, failed, no_answer)
- Call duration and qualification time
- ASR/TTS latency
- Error counts and types

**Business KPIs:**
- Qualification rate
- Handoff rate
- Sentiment distribution
- Language usage

**System Metrics:**
- Active calls
- API latency
- Error rates
- External service latency

### API Endpoints

```http
# Get current metrics
GET /api/v1/analytics/metrics

# Get daily metrics
GET /api/v1/analytics/metrics/daily/2024-10-24

# Get metrics range
GET /api/v1/analytics/metrics/range?start_date=2024-10-17&end_date=2024-10-24

# Get call analytics
GET /api/v1/analytics/calls?start_date=2024-10-17

# Manually aggregate metrics
POST /api/v1/analytics/metrics/aggregate/2024-10-24

# Get active alerts
GET /api/v1/analytics/alerts
```

### Recording Metrics

```python
from app.services.metrics_service import MetricsService
from app.models.metrics import CallMetrics

metrics_service = MetricsService(db)

# Record call metrics
call_metrics = CallMetrics(
    call_id="call_123",
    lead_id="lead_456",
    start_time=datetime.now(),
    end_time=datetime.now(),
    duration_seconds=180,
    status="completed",
    direction="outbound",
    language="hinglish",
    asr_latency_ms=234.5,
    tts_latency_ms=156.2,
    total_turns=12,
    qualification_completed=True,
    handoff_triggered=True,
    sentiment_score=0.75
)

await metrics_service.record_call_metrics(call_metrics)
```

### Daily Aggregation

Metrics are automatically aggregated daily. You can also trigger manual aggregation:

```python
# Aggregate metrics for a specific date
daily_metrics = await metrics_service.aggregate_daily_metrics("2024-10-24")
```

## Alerting System

### Alert Types

1. **High Error Rate** (>5%)
   - Severity: Critical
   - Triggers when error rate exceeds 5%

2. **High API Latency** (>2000ms)
   - Severity: Warning
   - Triggers when ASR/TTS latency exceeds 2 seconds

3. **High Call Failure Rate** (>10%)
   - Severity: Critical
   - Triggers when call failure rate exceeds 10%

### Configuration

#### Email Alerts

Set environment variables:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_FROM=alerts@voiceagent.com
ALERT_EMAIL_TO=ops@company.com,dev@company.com
```

#### Slack Alerts

Set Slack webhook URL:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Testing Alerts

```python
from app.services.alert_service import AlertService

alert_service = AlertService()

# Send test alert
results = await alert_service.send_test_alert()
# Returns: {"email": True, "slack": True}
```

### Manual Alerts

```python
# Send custom alert
await alert_service.send_alert(
    alert_type="custom_metric",
    severity="warning",
    message="Custom alert message",
    current_value=75.5,
    threshold_value=50.0,
    metadata={"additional": "context"}
)
```

### Automated Alert Checking

Run the background task periodically (e.g., every 5 minutes):

```python
from app.services.alert_service import check_and_send_alerts

# In your scheduler or background worker
await check_and_send_alerts(db)
```

## Monitoring Dashboard

The frontend provides real-time monitoring:

- **Dashboard**: Overview of key metrics
- **Analytics Page**: Detailed charts and trends
- **Alerts**: Active system alerts

Access at: `http://localhost:3000/analytics`

## Best Practices

### Logging

1. **Use appropriate log levels**
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for potentially harmful situations
   - ERROR: Error messages for serious problems
   - CRITICAL: Critical messages for very serious errors

2. **Include context**
   - Always set call_id and lead_id when available
   - Add relevant metadata to log entries

3. **Avoid logging sensitive data**
   - Don't log passwords, tokens, or PII
   - Use encryption service for sensitive fields

### Metrics

1. **Record metrics consistently**
   - Record metrics for every call
   - Include all relevant performance data

2. **Aggregate regularly**
   - Run daily aggregation jobs
   - Keep raw metrics for at least 30 days

3. **Monitor trends**
   - Track metrics over time
   - Set up alerts for anomalies

### Alerting

1. **Configure thresholds appropriately**
   - Adjust based on your SLAs
   - Avoid alert fatigue

2. **Test alert channels**
   - Verify email and Slack configuration
   - Run test alerts regularly

3. **Respond to alerts promptly**
   - Set up on-call rotation
   - Document response procedures

## Troubleshooting

### Logs not appearing

- Check LOG_LEVEL environment variable
- Verify logging is initialized in main.py
- Check file permissions if using LOG_FILE

### Metrics not collecting

- Ensure metrics are being recorded after each call
- Check database connection
- Verify MetricsService is initialized

### Alerts not sending

- Verify SMTP credentials for email
- Check Slack webhook URL
- Test with `send_test_alert()`
- Review logs for error messages

## Integration with External Tools

### Log Aggregation

Export logs to external services:

- **Elasticsearch**: Parse JSON logs with Logstash
- **Splunk**: Forward logs via HTTP Event Collector
- **CloudWatch**: Use AWS CloudWatch agent
- **Datadog**: Use Datadog agent with JSON parsing

### Metrics Visualization

- **Grafana**: Query MongoDB metrics collection
- **Prometheus**: Export metrics via custom exporter
- **Datadog**: Send metrics via StatsD

### Alert Management

- **PagerDuty**: Forward critical alerts
- **Opsgenie**: Integrate via webhook
- **VictorOps**: Use email integration

## Performance Considerations

- Logging is asynchronous and non-blocking
- Metrics are written to database in batches
- Alerts are rate-limited to prevent spam
- Old metrics can be archived after 90 days

## Security

- Logs are stored securely with restricted access
- Sensitive data is masked in logs
- Alert channels use encrypted connections
- Metrics database has authentication enabled

# AI Voice Loan Agent - Operator Runbook

## Table of Contents

1. [Emergency Contacts](#emergency-contacts)
2. [System Overview](#system-overview)
3. [Common Issues and Resolutions](#common-issues-and-resolutions)
4. [Escalation Procedures](#escalation-procedures)
5. [Backup and Recovery](#backup-and-recovery)
6. [Monitoring and Alerts](#monitoring-and-alerts)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Performance Tuning](#performance-tuning)
9. [Security Incidents](#security-incidents)
10. [Disaster Recovery](#disaster-recovery)

## Emergency Contacts

### On-Call Rotation

| Role                | Primary       | Secondary    | Phone       | Email                     |
| ------------------- | ------------- | ------------ | ----------- | ------------------------- |
| **Technical Lead**  | John Doe      | Jane Smith   | +1-555-0101 | john.doe@company.com      |
| **DevOps Engineer** | Mike Johnson  | Sarah Wilson | +1-555-0102 | mike.johnson@company.com  |
| **Product Manager** | Lisa Chen     | David Brown  | +1-555-0103 | lisa.chen@company.com     |
| **Business Owner**  | Robert Taylor | Emily Davis  | +1-555-0104 | robert.taylor@company.com |

### External Vendors

| Service           | Contact      | Phone           | Support Portal                   |
| ----------------- | ------------ | --------------- | -------------------------------- |
| **Twilio**        | Support Team | +1-888-TWILIO   | https://support.twilio.com       |
| **MongoDB Atlas** | Support Team | +1-866-237-8815 | https://support.mongodb.com      |
| **Google Cloud**  | Support Team | +1-855-836-3987 | https://cloud.google.com/support |
| **Sarvam AI**     | Support Team | +91-80-SARVAM   | https://support.sarvam.ai        |

### Escalation Matrix

| Severity          | Response Time | Escalation Time | Escalation To           |
| ----------------- | ------------- | --------------- | ----------------------- |
| **P0 - Critical** | 15 minutes    | 30 minutes      | Technical Lead + DevOps |
| **P1 - High**     | 1 hour        | 2 hours         | Technical Lead          |
| **P2 - Medium**   | 4 hours       | 8 hours         | Team Lead               |
| **P3 - Low**      | 24 hours      | 48 hours        | Product Manager         |

## System Overview

### Architecture Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Load Balancer  │    │   Frontend       │    │   Backend       │
│  (NGINX/ALB)    │◄──►│   (React)        │◄──►│   (FastAPI)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────┐
                       │                                 │                 │
               ┌───────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐  ┌──────▼──────┐
               │   MongoDB    │  │  Twilio   │  │  Google     │  │  Sarvam AI  │
               │   (Database) │  │ (Telephony)│  │  Cloud      │  │  (Speech)   │
               └──────────────┘  └───────────┘  └─────────────┘  └─────────────┘
```

### Key Services

- **Frontend**: React application serving the dashboard
- **Backend**: FastAPI application handling business logic
- **Database**: MongoDB storing leads, calls, and conversations
- **Telephony**: Twilio for voice calls and webhooks
- **Speech**: Google Cloud Speech + Sarvam AI for ASR/TTS
- **Notifications**: SuprSend/Gupshup for WhatsApp/SMS

### Critical Dependencies

1. **MongoDB Atlas** - Primary data store
2. **Twilio** - Voice calling infrastructure
3. **Google Cloud Speech** - Speech recognition and synthesis
4. **Sarvam AI** - Indian language speech processing
5. **OpenAI API** - Natural language understanding

## Common Issues and Resolutions

### 1. Call Connection Issues

#### Symptom: Calls not connecting or immediately dropping

**Immediate Actions:**

```bash
# Check Twilio service status
curl -s https://status.twilio.com/api/v2/status.json | jq '.status.indicator'

# Verify webhook endpoint
curl -X POST https://api.yourdomain.com/api/v1/calls/inbound/webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=test&From=+1234567890&CallStatus=ringing"

# Check backend logs for webhook errors
kubectl logs -f deployment/backend-deployment -n voice-agent | grep webhook
```

**Root Causes & Solutions:**

| Cause                      | Symptoms                           | Solution                                        |
| -------------------------- | ---------------------------------- | ----------------------------------------------- |
| Webhook URL unreachable    | HTTP 5xx errors in Twilio debugger | Check load balancer, DNS, SSL certificate       |
| Invalid Twilio credentials | Authentication errors              | Verify TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN |
| Rate limiting              | 429 errors                         | Check rate limits, scale backend pods           |
| Network connectivity       | Timeout errors                     | Check firewall rules, security groups           |

**Resolution Steps:**

1. Check Twilio Console Debugger: https://console.twilio.com/us1/develop/voice/manage/debugger
2. Verify webhook URL responds with valid TwiML
3. Check backend pod health and logs
4. Test with a manual call using Twilio CLI

### 2. Speech Recognition Failures

#### Symptom: Poor ASR accuracy or TTS generation failures

**Immediate Actions:**

```bash
# Check Google Cloud Speech API status
gcloud services list --enabled | grep speech

# Test Sarvam AI connectivity
curl -H "Authorization: Bearer $SARVAM_API_KEY" \
  https://api.sarvam.ai/speech-to-text

# Check speech service logs
kubectl logs -f deployment/backend-deployment -n voice-agent | grep "speech\|asr\|tts"
```

**Root Causes & Solutions:**

| Cause                      | Symptoms                 | Solution                                             |
| -------------------------- | ------------------------ | ---------------------------------------------------- |
| API quota exceeded         | 429 quota errors         | Check quotas in GCP/Sarvam console, request increase |
| Invalid credentials        | 401/403 errors           | Verify service account keys, API keys                |
| Audio quality issues       | Low confidence scores    | Check audio format, sample rate, noise levels        |
| Language detection failure | Wrong language responses | Verify language codes, fallback logic                |

**Resolution Steps:**

1. Check API quotas and usage in respective consoles
2. Verify audio format compatibility (16kHz, mono, linear16)
3. Test with known good audio samples
4. Enable fallback to alternative speech provider

### 3. Database Connection Issues

#### Symptom: MongoDB connection timeouts or failures

**Immediate Actions:**

```bash
# Test MongoDB connectivity
mongosh "$MONGODB_URI" --eval "db.adminCommand('ping')"

# Check connection pool status
kubectl exec -it deployment/backend-deployment -n voice-agent -- python -c "
from app.database import get_database
import asyncio
async def test():
    try:
        db = await get_database()
        result = await db.command('ping')
        print('Database connection: OK')
    except Exception as e:
        print(f'Database connection failed: {e}')
asyncio.run(test())
"
```

**Root Causes & Solutions:**

| Cause                      | Symptoms            | Solution                                                 |
| -------------------------- | ------------------- | -------------------------------------------------------- |
| Network connectivity       | Connection timeouts | Check VPC peering, security groups, IP whitelist         |
| Authentication failure     | Auth errors         | Verify username/password, connection string              |
| Connection pool exhaustion | Pool timeout errors | Increase maxPoolSize, check for connection leaks         |
| MongoDB Atlas maintenance  | Service unavailable | Check Atlas status page, wait for maintenance completion |

**Resolution Steps:**

1. Check MongoDB Atlas status: https://status.mongodb.com/
2. Verify IP whitelist includes current server IPs
3. Test connection from different network
4. Check connection pool configuration and metrics

### 4. High API Latency

#### Symptom: Slow response times, timeout errors

**Immediate Actions:**

```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/health

# Monitor backend pod resources
kubectl top pods -n voice-agent

# Check database query performance
mongosh "$MONGODB_URI" --eval "db.setProfilingLevel(2, {slowms: 100})"
```

**Root Causes & Solutions:**

| Cause                 | Symptoms                     | Solution                                 |
| --------------------- | ---------------------------- | ---------------------------------------- |
| High CPU usage        | >80% CPU utilization         | Scale pods horizontally, optimize code   |
| Memory pressure       | High memory usage, OOM kills | Increase memory limits, fix memory leaks |
| Slow database queries | High query execution time    | Add indexes, optimize queries            |
| External API latency  | Slow third-party responses   | Implement caching, circuit breakers      |

**Resolution Steps:**

1. Scale backend pods: `kubectl scale deployment backend-deployment --replicas=5 -n voice-agent`
2. Check slow queries in MongoDB profiler
3. Monitor external API response times
4. Enable caching for frequently accessed data

### 5. Authentication Issues

#### Symptom: 401/403 errors, login failures

**Immediate Actions:**

```bash
# Test JWT token generation
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Verify JWT secret configuration
kubectl get secret voice-agent-secrets -n voice-agent -o yaml | grep jwt-secret
```

**Root Causes & Solutions:**

| Cause              | Symptoms                   | Solution                                   |
| ------------------ | -------------------------- | ------------------------------------------ |
| Invalid JWT secret | Token validation failures  | Verify JWT_SECRET_KEY in environment       |
| Expired tokens     | 401 errors for valid users | Check token expiration time, refresh logic |
| Clock skew         | Intermittent auth failures | Sync server clocks with NTP                |
| CORS issues        | Browser auth failures      | Check CORS_ORIGINS configuration           |

### 6. Notification Delivery Failures

#### Symptom: WhatsApp/SMS not being sent

**Immediate Actions:**

```bash
# Test notification service
curl -X POST https://api.yourdomain.com/api/v1/notifications/test \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"phone":"+919876543210","message":"test"}'

# Check notification logs
kubectl logs -f deployment/backend-deployment -n voice-agent | grep notification
```

**Root Causes & Solutions:**

| Cause                   | Symptoms                          | Solution                                 |
| ----------------------- | --------------------------------- | ---------------------------------------- |
| Invalid API credentials | 401/403 from notification service | Verify SuprSend/Gupshup API keys         |
| Rate limiting           | 429 errors                        | Implement retry logic, check rate limits |
| Invalid phone numbers   | Delivery failures                 | Validate phone number format             |
| Template issues         | Template not found errors         | Verify WhatsApp template approval status |

## Escalation Procedures

### Severity Definitions

#### P0 - Critical (System Down)

- **Definition**: Complete system outage, no calls can be made/received
- **Examples**:
  - All backend pods crashed
  - Database completely unavailable
  - Twilio service down
- **Response**: Immediate (15 minutes)
- **Escalation**: Technical Lead + DevOps + Business Owner

#### P1 - High (Major Feature Broken)

- **Definition**: Core functionality impacted, significant user impact
- **Examples**:
  - Speech recognition not working
  - High call failure rate (>20%)
  - Authentication system down
- **Response**: 1 hour
- **Escalation**: Technical Lead + DevOps

#### P2 - Medium (Minor Feature Issues)

- **Definition**: Some features impacted, workaround available
- **Examples**:
  - Dashboard loading slowly
  - Some notifications not sending
  - Non-critical API endpoints failing
- **Response**: 4 hours
- **Escalation**: Team Lead

#### P3 - Low (Cosmetic Issues)

- **Definition**: Minor issues, no significant impact
- **Examples**:
  - UI display issues
  - Non-critical logging errors
  - Performance optimization opportunities
- **Response**: 24 hours
- **Escalation**: Product Manager

### Escalation Process

1. **Initial Response** (On-call engineer)
   - Acknowledge alert within response time
   - Begin initial investigation
   - Update incident status

2. **Assessment** (15-30 minutes)
   - Determine severity level
   - Identify affected components
   - Estimate impact and timeline

3. **Escalation Decision**
   - If resolution time exceeds escalation threshold
   - If additional expertise needed
   - If business impact is higher than initially assessed

4. **Communication**
   - Update stakeholders every 30 minutes for P0/P1
   - Use incident communication channels
   - Document all actions taken

### Incident Communication Template

```
INCIDENT UPDATE - [SEVERITY] - [TIMESTAMP]

Status: [INVESTIGATING/IDENTIFIED/MONITORING/RESOLVED]
Impact: [Description of user impact]
Affected Services: [List of affected components]
Root Cause: [If identified]
Next Update: [Timestamp]
ETA for Resolution: [If known]

Actions Taken:
- [Action 1]
- [Action 2]

Next Steps:
- [Next action]
- [Responsible person]
```

## Backup and Recovery

### Backup Strategy

#### 1. Database Backups

**Automated Daily Backups:**

```bash
#!/bin/bash
# /opt/scripts/backup_mongodb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"
S3_BUCKET="voice-agent-backups"

# Create backup
mongodump --uri="$MONGODB_URI" --out="$BACKUP_DIR/backup_$DATE"

# Compress and upload
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" -C "$BACKUP_DIR" "backup_$DATE"
aws s3 cp "$BACKUP_DIR/backup_$DATE.tar.gz" "s3://$S3_BUCKET/mongodb/"

# Cleanup local files
rm -rf "$BACKUP_DIR/backup_$DATE"
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

# Verify backup
aws s3 ls "s3://$S3_BUCKET/mongodb/backup_$DATE.tar.gz"
```

**Backup Schedule:**

- **Daily**: Full database backup at 2 AM UTC
- **Weekly**: Full system backup including configurations
- **Monthly**: Long-term archive backup

#### 2. Configuration Backups

```bash
#!/bin/bash
# /opt/scripts/backup_configs.sh

DATE=$(date +%Y%m%d_%H%M%S)
CONFIG_DIR="/backups/configs"

# Backup Kubernetes configurations
kubectl get all -n voice-agent -o yaml > "$CONFIG_DIR/k8s_resources_$DATE.yaml"
kubectl get secrets -n voice-agent -o yaml > "$CONFIG_DIR/k8s_secrets_$DATE.yaml"
kubectl get configmaps -n voice-agent -o yaml > "$CONFIG_DIR/k8s_configmaps_$DATE.yaml"

# Backup environment files
cp /opt/voice-agent/.env.prod "$CONFIG_DIR/env_prod_$DATE"

# Upload to S3
aws s3 sync "$CONFIG_DIR" "s3://voice-agent-backups/configs/"
```

### Recovery Procedures

#### 1. Database Recovery

**Complete Database Restore:**

```bash
#!/bin/bash
# restore_mongodb.sh

BACKUP_FILE="$1"  # e.g., backup_20251024_020000.tar.gz
TEMP_DIR="/tmp/mongodb_restore"

# Download and extract backup
aws s3 cp "s3://voice-agent-backups/mongodb/$BACKUP_FILE" "$TEMP_DIR/"
tar -xzf "$TEMP_DIR/$BACKUP_FILE" -C "$TEMP_DIR"

# Stop application to prevent writes
kubectl scale deployment backend-deployment --replicas=0 -n voice-agent

# Restore database
mongorestore --uri="$MONGODB_URI" --drop "$TEMP_DIR/backup_*/voice_agent_prod"

# Restart application
kubectl scale deployment backend-deployment --replicas=3 -n voice-agent

# Verify restoration
mongosh "$MONGODB_URI" --eval "db.leads.countDocuments()"
```

**Point-in-Time Recovery:**

```bash
# For MongoDB Atlas with continuous backup
# 1. Go to Atlas console
# 2. Select cluster -> Backup tab
# 3. Choose restore point
# 4. Create new cluster or restore to existing
# 5. Update connection string in application
```

#### 2. Application Recovery

**Rolling Back Deployment:**

```bash
# Check deployment history
kubectl rollout history deployment/backend-deployment -n voice-agent

# Rollback to previous version
kubectl rollout undo deployment/backend-deployment -n voice-agent

# Rollback to specific revision
kubectl rollout undo deployment/backend-deployment --to-revision=2 -n voice-agent

# Monitor rollback status
kubectl rollout status deployment/backend-deployment -n voice-agent
```

**Complete System Recovery:**

```bash
#!/bin/bash
# disaster_recovery.sh

# 1. Restore Kubernetes resources
kubectl apply -f /backups/configs/k8s_resources_latest.yaml

# 2. Restore secrets and configmaps
kubectl apply -f /backups/configs/k8s_secrets_latest.yaml
kubectl apply -f /backups/configs/k8s_configmaps_latest.yaml

# 3. Restore database (if needed)
./restore_mongodb.sh backup_latest.tar.gz

# 4. Verify all services are running
kubectl get pods -n voice-agent
kubectl get services -n voice-agent

# 5. Run health checks
curl https://api.yourdomain.com/health
```

### Recovery Testing

**Monthly Recovery Drills:**

```bash
#!/bin/bash
# recovery_test.sh

# 1. Create test environment
kubectl create namespace voice-agent-test

# 2. Deploy application with test configuration
kubectl apply -f k8s/ -n voice-agent-test

# 3. Restore latest backup to test database
./restore_mongodb.sh backup_latest.tar.gz test_mongodb_uri

# 4. Run smoke tests
python tests/smoke_tests.py --env=test

# 5. Cleanup test environment
kubectl delete namespace voice-agent-test
```

## Monitoring and Alerts

### Key Metrics Dashboard

#### System Health Metrics

- **Pod Status**: Running/Failed pods count
- **CPU Usage**: Average CPU utilization across pods
- **Memory Usage**: Memory consumption and limits
- **Disk Usage**: Storage utilization
- **Network I/O**: Ingress/egress traffic

#### Application Metrics

- **API Response Time**: 95th percentile response time
- **Error Rate**: 4xx/5xx error percentage
- **Call Volume**: Calls per minute/hour
- **Call Success Rate**: Successful call completion percentage
- **Speech Recognition Accuracy**: ASR confidence scores

#### Business Metrics

- **Lead Qualification Rate**: Percentage of calls resulting in qualified leads
- **Handoff Rate**: Percentage of calls transferred to humans
- **Average Call Duration**: Mean call length
- **Sentiment Distribution**: Positive/neutral/negative sentiment breakdown
- **Language Usage**: Distribution of languages used

### Alert Thresholds

#### Critical Alerts (P0)

```yaml
# prometheus/alerts.yml
- alert: SystemDown
  expr: up{job="voice-agent-backend"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Voice Agent system is down"

- alert: DatabaseDown
  expr: mongodb_up == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "MongoDB is unreachable"

- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate: {{ $value }}%"
```

#### Warning Alerts (P1)

```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High API latency: {{ $value }}s"

- alert: CallFailureRate
  expr: rate(calls_failed_total[5m]) / rate(calls_total[5m]) > 0.2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High call failure rate: {{ $value }}%"

- alert: LowASRAccuracy
  expr: avg(asr_confidence_score) < 0.8
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Low ASR accuracy: {{ $value }}"
```

### Alert Response Procedures

#### 1. Critical Alert Response

```bash
# Immediate actions for P0 alerts
1. Acknowledge alert in PagerDuty/Slack
2. Check system status dashboard
3. Verify alert is not false positive
4. Begin incident response procedure
5. Notify stakeholders if confirmed outage
```

#### 2. Warning Alert Response

```bash
# Actions for P1 alerts
1. Investigate root cause
2. Check related metrics and logs
3. Determine if immediate action needed
4. Document findings
5. Schedule fix if non-urgent
```

## Maintenance Procedures

### Scheduled Maintenance Windows

**Weekly Maintenance (Sundays 2-4 AM UTC):**

- Security updates
- Log rotation
- Database optimization
- Performance tuning

**Monthly Maintenance (First Sunday 2-6 AM UTC):**

- Major updates
- Backup verification
- Disaster recovery testing
- Capacity planning review

### Pre-Maintenance Checklist

```bash
#!/bin/bash
# pre_maintenance.sh

echo "=== Pre-Maintenance Checklist ==="

# 1. Verify backup completion
echo "Checking latest backup..."
aws s3 ls s3://voice-agent-backups/mongodb/ | tail -1

# 2. Check system health
echo "Checking system health..."
kubectl get pods -n voice-agent
curl -s https://api.yourdomain.com/health | jq '.status'

# 3. Notify stakeholders
echo "Sending maintenance notification..."
# Send notification to stakeholders

# 4. Scale down non-critical services
echo "Scaling down non-critical services..."
kubectl scale deployment frontend-deployment --replicas=1 -n voice-agent

# 5. Enable maintenance mode
echo "Enabling maintenance mode..."
kubectl patch configmap app-config -n voice-agent -p '{"data":{"maintenance_mode":"true"}}'
```

### Post-Maintenance Checklist

```bash
#!/bin/bash
# post_maintenance.sh

echo "=== Post-Maintenance Checklist ==="

# 1. Disable maintenance mode
kubectl patch configmap app-config -n voice-agent -p '{"data":{"maintenance_mode":"false"}}'

# 2. Scale services back up
kubectl scale deployment frontend-deployment --replicas=3 -n voice-agent
kubectl scale deployment backend-deployment --replicas=3 -n voice-agent

# 3. Run health checks
echo "Running health checks..."
./scripts/health_check.sh

# 4. Test critical functionality
echo "Testing critical functionality..."
python tests/smoke_tests.py

# 5. Monitor for issues
echo "Monitoring system for 30 minutes..."
# Monitor alerts and metrics

# 6. Notify completion
echo "Sending maintenance completion notification..."
```

## Performance Tuning

### Database Optimization

#### Index Optimization

```javascript
// Check index usage
db.leads.aggregate([{ $indexStats: {} }]);

// Create missing indexes
db.leads.createIndex({ phone: 1, status: 1 });
db.calls.createIndex({ lead_id: 1, created_at: -1 });
db.conversations.createIndex({ call_id: 1 });

// Remove unused indexes
db.leads.dropIndex("unused_index_name");
```

#### Query Optimization

```javascript
// Analyze slow queries
db.setProfilingLevel(2, { slowms: 100 });
db.system.profile.find().sort({ ts: -1 }).limit(5);

// Optimize aggregation pipelines
db.leads
  .explain("executionStats")
  .aggregate([
    { $match: { status: "qualified" } },
    { $group: { _id: "$country", count: { $sum: 1 } } },
  ]);
```

### Application Optimization

#### Connection Pool Tuning

```python
# MongoDB connection pool optimization
client = AsyncIOMotorClient(
    mongodb_uri,
    maxPoolSize=50,        # Increase for high load
    minPoolSize=10,        # Maintain minimum connections
    maxIdleTimeMS=30000,   # Close idle connections
    waitQueueTimeoutMS=5000  # Timeout for getting connection
)
```

#### Caching Implementation

```python
# Redis caching for frequently accessed data
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)

            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(expiration=1800)
async def get_prompts_by_language(language: str):
    # Expensive database query
    pass
```

### Infrastructure Scaling

#### Horizontal Pod Autoscaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-deployment
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

## Security Incidents

### Incident Classification

#### Security Incident Types

1. **Data Breach**: Unauthorized access to customer data
2. **System Compromise**: Unauthorized access to systems
3. **DDoS Attack**: Denial of service attacks
4. **Malware**: Malicious software detected
5. **Insider Threat**: Suspicious internal activity

### Incident Response Procedure

#### 1. Detection and Analysis (0-1 hour)

```bash
# Immediate actions upon security alert
1. Isolate affected systems
   kubectl cordon <affected-node>
   kubectl drain <affected-node> --ignore-daemonsets

2. Preserve evidence
   kubectl logs deployment/backend-deployment > incident_logs_$(date +%Y%m%d_%H%M%S).txt

3. Assess scope and impact
   # Check access logs, authentication logs, database access

4. Notify security team and management
```

#### 2. Containment (1-4 hours)

```bash
# Contain the incident
1. Block malicious IPs
   kubectl patch service backend-service -p '{"spec":{"loadBalancerSourceRanges":["trusted.ip.range/24"]}}'

2. Rotate compromised credentials
   kubectl delete secret voice-agent-secrets
   kubectl create secret generic voice-agent-secrets --from-env-file=.env.new

3. Enable additional monitoring
   # Increase log levels, enable audit logging

4. Implement temporary access controls
```

#### 3. Eradication and Recovery (4-24 hours)

```bash
# Remove threats and restore services
1. Patch vulnerabilities
   # Update container images, apply security patches

2. Rebuild compromised systems
   kubectl delete deployment backend-deployment
   kubectl apply -f k8s/backend-deployment.yaml

3. Restore from clean backups if needed
   ./restore_mongodb.sh clean_backup.tar.gz

4. Verify system integrity
   # Run security scans, verify configurations
```

#### 4. Post-Incident Activities (1-7 days)

```bash
# Document and improve
1. Document timeline and actions
2. Conduct post-mortem meeting
3. Update security procedures
4. Implement additional controls
5. Train team on lessons learned
```

### Security Monitoring

#### Log Analysis

```bash
# Monitor for suspicious activities
# Failed authentication attempts
kubectl logs deployment/backend-deployment | grep "authentication failed" | tail -20

# Unusual API access patterns
kubectl logs deployment/backend-deployment | grep "rate_limit_exceeded" | tail -20

# Database access anomalies
mongosh "$MONGODB_URI" --eval "db.audit.find({action: 'unauthorized_access'}).sort({timestamp: -1}).limit(10)"
```

#### Security Alerts

```yaml
# Security-specific alerts
- alert: MultipleFailedLogins
  expr: rate(auth_failures_total[5m]) > 10
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Multiple failed login attempts detected"

- alert: UnauthorizedAPIAccess
  expr: rate(http_requests_total{status="403"}[5m]) > 5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High rate of unauthorized API access"

- alert: SuspiciousDataAccess
  expr: rate(database_queries_total{type="sensitive"}[10m]) > 100
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Unusual database access pattern detected"
```

## Disaster Recovery

### Disaster Scenarios

#### 1. Complete Data Center Outage

**Recovery Time Objective (RTO)**: 4 hours
**Recovery Point Objective (RPO)**: 1 hour

**Recovery Steps:**

```bash
# 1. Activate secondary region
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 \
  --change-batch file://failover-dns.json

# 2. Deploy application in DR region
kubectl config use-context dr-cluster
kubectl apply -f k8s/ -n voice-agent

# 3. Restore database from latest backup
./restore_mongodb.sh latest_backup.tar.gz $DR_MONGODB_URI

# 4. Update external service configurations
# Update Twilio webhook URLs to DR region
# Update DNS records to point to DR region

# 5. Verify functionality
./scripts/dr_verification.sh
```

#### 2. Database Corruption

**RTO**: 2 hours
**RPO**: 15 minutes (continuous backup)

**Recovery Steps:**

```bash
# 1. Stop all write operations
kubectl scale deployment backend-deployment --replicas=0

# 2. Assess corruption extent
mongosh "$MONGODB_URI" --eval "db.runCommand({validate: 'leads'})"

# 3. Restore from point-in-time backup
# Use MongoDB Atlas point-in-time recovery
# Or restore from latest clean backup

# 4. Verify data integrity
python scripts/verify_data_integrity.py

# 5. Resume operations
kubectl scale deployment backend-deployment --replicas=3
```

#### 3. Security Breach

**RTO**: 6 hours
**RPO**: 0 (no data loss acceptable)

**Recovery Steps:**

```bash
# 1. Immediate isolation
kubectl delete ingress voice-agent-ingress
kubectl patch service backend-service -p '{"spec":{"type":"ClusterIP"}}'

# 2. Forensic analysis
kubectl cp backend-pod:/var/log/app.log ./forensic_logs/
# Analyze logs, identify breach vector

# 3. Clean rebuild
# Rebuild all containers from clean base images
# Rotate all secrets and credentials
# Restore from pre-breach backup if needed

# 4. Enhanced security deployment
kubectl apply -f k8s/security-hardened/
# Deploy with additional security controls

# 5. Gradual service restoration
# Restore services one by one with monitoring
# Verify no ongoing threats
```

### DR Testing Schedule

**Quarterly DR Tests:**

- **Q1**: Database failover test
- **Q2**: Complete region failover test
- **Q3**: Security incident simulation
- **Q4**: Full disaster recovery drill

**Monthly Tests:**

- Backup restoration verification
- Failover procedure validation
- Communication plan testing

### DR Checklist

#### Pre-Disaster Preparation

- [ ] Backup verification completed
- [ ] DR environment ready and tested
- [ ] Contact lists updated
- [ ] Procedures documented and accessible
- [ ] External services configured for failover

#### During Disaster

- [ ] Incident commander assigned
- [ ] Stakeholders notified
- [ ] Recovery procedures initiated
- [ ] Progress tracked and communicated
- [ ] External services updated

#### Post-Disaster

- [ ] Services fully restored
- [ ] Data integrity verified
- [ ] Performance validated
- [ ] Lessons learned documented
- [ ] Procedures updated

This operator runbook provides comprehensive guidance for managing the AI Voice Loan Agent system, covering common issues, escalation procedures, backup and recovery, monitoring, maintenance, performance tuning, security incidents, and disaster recovery scenarios.

# AI Voice Loan Agent - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [External Service Configuration](#external-service-configuration)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

**Development Environment:**

- Docker 20.10+ and Docker Compose 2.0+
- Node.js 18+ (for frontend development)
- Python 3.10+ (for backend development)
- Git 2.30+

**Production Environment:**

- Kubernetes 1.24+ cluster
- MongoDB 6.0+ (Atlas recommended)
- Load balancer (NGINX/AWS ALB)
- SSL certificates
- Domain name with DNS access

### External Services

**Required Services:**

- **Twilio Account**: For telephony services
- **Google Cloud Platform** or **AWS**: For speech services (ASR/TTS)
- **Sarvam AI Account**: For Indian language speech processing
- **MongoDB Atlas**: For production database
- **SuprSend** or **Gupshup**: For WhatsApp/SMS notifications
- **OpenAI API**: For NLU and sentiment analysis

**Optional Services:**

- **Sentry**: For error tracking
- **DataDog/New Relic**: For APM monitoring
- **CloudFlare**: For CDN and DDoS protection

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ai-voice-loan-agent.git
cd ai-voice-loan-agent
```

### 2. Environment Configuration

Copy environment files and configure:

```bash
# Backend environment
cp backend/.env.example backend/.env
# Frontend environment
cp frontend/.env.example frontend/.env
# Root environment
cp .env.example .env
```

Edit `backend/.env`:

```bash
# Database
MONGODB_URI=mongodb://localhost:27017/voice_agent_dev

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-ngrok-url.ngrok.io/api/v1/calls/inbound/webhook

# Speech Services
GOOGLE_CLOUD_PROJECT_ID=your_gcp_project
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_BASE_URL=https://api.sarvam.ai

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Notifications
SUPRSEND_API_KEY=your_suprsend_key
SUPRSEND_API_SECRET=your_suprsend_secret

# Security
JWT_SECRET_KEY=your_jwt_secret_key_min_32_chars
API_KEY_WEBHOOK=your_webhook_api_key

# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000
```

Edit `frontend/.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

### 3. Start Development Environment

Using Docker Compose (Recommended):

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Manual Setup (Alternative):

```bash
# Start MongoDB
docker run -d --name mongo -p 27017:27017 mongo:6.0

# Start Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Start Frontend (new terminal)
cd frontend
npm install
npm start
```

### 4. Initialize Database

```bash
# Run database initialization
docker-compose exec backend python app/init_db.py

# Seed test data (optional)
docker-compose exec backend python seed_data.py
```

### 5. Verify Installation

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB**: mongodb://localhost:27017

Test API endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

### 6. Development Workflow

**Backend Development:**

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run tests
pytest

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Development:**

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Production Deployment

### Option 1: Kubernetes Deployment (Recommended)

#### 1. Prepare Kubernetes Cluster

```bash
# Create namespace
kubectl create namespace voice-agent

# Create secrets
kubectl create secret generic voice-agent-secrets \
  --from-literal=mongodb-uri="mongodb+srv://user:pass@cluster.mongodb.net/voice_agent" \
  --from-literal=twilio-account-sid="your_sid" \
  --from-literal=twilio-auth-token="your_token" \
  --from-literal=openai-api-key="your_key" \
  --from-literal=jwt-secret="your_jwt_secret" \
  --namespace=voice-agent
```

#### 2. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/ -n voice-agent

# Check deployment status
kubectl get pods -n voice-agent
kubectl get services -n voice-agent
```

#### 3. Configure Ingress

Update `k8s/ingress.yaml` with your domain:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: voice-agent-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.yourdomain.com
        - app.yourdomain.com
      secretName: voice-agent-tls
  rules:
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-service
                port:
                  number: 8000
    - host: app.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

### Option 2: Docker Compose Production

#### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - MONGODB_URI=${MONGODB_URI}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
    env_file:
      - .env.prod
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  app_data:
```

#### 2. Deploy Production

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Environment Configuration

### Production Environment Variables

Create `.env.prod`:

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/voice_agent_prod

# Security
JWT_SECRET_KEY=your_production_jwt_secret_min_32_chars
API_KEY_WEBHOOK=your_production_webhook_api_key
CORS_ORIGINS=https://app.yourdomain.com

# External Services
TWILIO_ACCOUNT_SID=your_production_twilio_sid
TWILIO_AUTH_TOKEN=your_production_twilio_token
TWILIO_PHONE_NUMBER=your_production_phone_number
TWILIO_WEBHOOK_URL=https://api.yourdomain.com/api/v1/calls/inbound/webhook

# Speech Services
GOOGLE_CLOUD_PROJECT_ID=your_production_gcp_project
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-service-account.json
SARVAM_API_KEY=your_production_sarvam_key

# OpenAI
OPENAI_API_KEY=your_production_openai_key

# Notifications
SUPRSEND_API_KEY=your_production_suprsend_key
SUPRSEND_API_SECRET=your_production_suprsend_secret

# Monitoring
SENTRY_DSN=your_sentry_dsn
DATADOG_API_KEY=your_datadog_key
```

### Security Configuration

#### 1. SSL/TLS Setup

For NGINX:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 2. Firewall Configuration

```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

## Database Setup

### MongoDB Atlas (Recommended)

#### 1. Create Cluster

1. Sign up at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new cluster (M10+ for production)
3. Configure network access (whitelist your server IPs)
4. Create database user with read/write permissions

#### 2. Initialize Database

```bash
# Connect to your cluster
mongosh "mongodb+srv://cluster.mongodb.net/voice_agent_prod" --username your_username

# Create indexes for performance
use voice_agent_prod

# Lead indexes
db.leads.createIndex({ "phone": 1 }, { unique: true })
db.leads.createIndex({ "status": 1, "created_at": -1 })
db.leads.createIndex({ "eligibility_category": 1 })

# Call indexes
db.calls.createIndex({ "lead_id": 1, "created_at": -1 })
db.calls.createIndex({ "status": 1, "created_at": -1 })
db.calls.createIndex({ "call_sid": 1 }, { unique: true, sparse: true })

# Conversation indexes
db.conversations.createIndex({ "call_id": 1 })
db.conversations.createIndex({ "lead_id": 1, "created_at": -1 })
```

### Self-Hosted MongoDB

#### 1. Install MongoDB

```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### 2. Configure MongoDB

Edit `/etc/mongod.conf`:

```yaml
net:
  port: 27017
  bindIp: 127.0.0.1,your_server_ip

security:
  authorization: enabled

replication:
  replSetName: "rs0"
```

#### 3. Initialize Replica Set

```bash
mongosh
rs.initiate()
```

## External Service Configuration

### Twilio Setup

#### 1. Configure Webhook URLs

In Twilio Console:

- **Voice URL**: `https://api.yourdomain.com/api/v1/calls/inbound/webhook`
- **Status Callback URL**: `https://api.yourdomain.com/api/v1/calls/status/webhook`
- **HTTP Method**: POST

#### 2. Configure Phone Number

```bash
# Using Twilio CLI
twilio phone-numbers:update +1234567890 \
  --voice-url=https://api.yourdomain.com/api/v1/calls/inbound/webhook \
  --voice-method=POST
```

### Google Cloud Speech Setup

#### 1. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create voice-agent-speech \
  --display-name="Voice Agent Speech Service"

# Grant permissions
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:voice-agent-speech@your-project-id.iam.gserviceaccount.com" \
  --role="roles/speech.admin"

# Create and download key
gcloud iam service-accounts keys create gcp-service-account.json \
  --iam-account=voice-agent-speech@your-project-id.iam.gserviceaccount.com
```

#### 2. Enable APIs

```bash
gcloud services enable speech.googleapis.com
gcloud services enable texttospeech.googleapis.com
```

### Sarvam AI Setup

#### 1. Get API Key

1. Sign up at [Sarvam AI](https://www.sarvam.ai/)
2. Generate API key from dashboard
3. Configure in environment variables

#### 2. Test Integration

```bash
curl -X POST "https://api.sarvam.ai/speech-to-text" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"language": "hi-IN", "audio_url": "test_audio_url"}'
```

## Monitoring and Alerting

### Application Monitoring

#### 1. Health Checks

The application provides health check endpoints:

```bash
# Application health
curl https://api.yourdomain.com/health

# Database health
curl https://api.yourdomain.com/health/db

# External services health
curl https://api.yourdomain.com/health/services
```

#### 2. Prometheus Metrics

Add to `docker-compose.prod.yml`:

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  command:
    - "--config.file=/etc/prometheus/prometheus.yml"
    - "--storage.tsdb.path=/prometheus"

grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana_data:/var/lib/grafana
```

#### 3. Log Aggregation

Configure log shipping to ELK stack:

```yaml
filebeat:
  image: docker.elastic.co/beats/filebeat:8.5.0
  volumes:
    - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

### Alerting Rules

#### 1. Prometheus Alerts

Create `alerts.yml`:

```yaml
groups:
  - name: voice_agent_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected

      - alert: CallFailureRate
        expr: rate(calls_failed_total[5m]) / rate(calls_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: High call failure rate

      - alert: DatabaseConnectionDown
        expr: up{job="mongodb"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Database connection is down
```

#### 2. Notification Channels

Configure Slack/Email notifications:

```yaml
# alertmanager.yml
route:
  group_by: ["alertname"]
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: "web.hook"

receivers:
  - name: "web.hook"
    slack_configs:
      - api_url: "your_slack_webhook_url"
        channel: "#alerts"
        title: "Voice Agent Alert"
        text: "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}"
```

### Performance Monitoring

#### 1. Key Metrics to Track

- **Call Metrics**: Volume, completion rate, duration
- **API Metrics**: Response time, error rate, throughput
- **Speech Metrics**: ASR accuracy, TTS latency
- **Business Metrics**: Qualification rate, handoff rate, sentiment scores

#### 2. Dashboard Setup

Import Grafana dashboard with key metrics:

```json
{
  "dashboard": {
    "title": "Voice Agent Monitoring",
    "panels": [
      {
        "title": "Call Volume",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(calls_total[5m])",
            "legendFormat": "Calls per second"
          }
        ]
      },
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Call Connection Issues

**Problem**: Calls not connecting or dropping

**Diagnosis**:

```bash
# Check Twilio webhook logs
docker-compose logs backend | grep "webhook"

# Test webhook endpoint
curl -X POST https://api.yourdomain.com/api/v1/calls/inbound/webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=test&From=+1234567890&CallStatus=ringing"

# Check Twilio debugger
# Visit: https://www.twilio.com/console/voice/debugger
```

**Solutions**:

- Verify webhook URL is accessible from internet
- Check Twilio account balance
- Verify phone number configuration
- Check firewall rules

#### 2. Speech Recognition Issues

**Problem**: Poor ASR accuracy or TTS failures

**Diagnosis**:

```bash
# Check speech service logs
docker-compose logs backend | grep "speech"

# Test Google Cloud credentials
gcloud auth application-default print-access-token

# Test Sarvam API
curl -H "Authorization: Bearer $SARVAM_API_KEY" \
  https://api.sarvam.ai/speech-to-text
```

**Solutions**:

- Verify API keys and credentials
- Check audio quality and format
- Test with different languages
- Monitor API quotas and limits

#### 3. Database Connection Issues

**Problem**: MongoDB connection failures

**Diagnosis**:

```bash
# Test MongoDB connection
mongosh "$MONGODB_URI"

# Check connection pool
docker-compose exec backend python -c "
from app.database import get_database
import asyncio
async def test():
    db = await get_database()
    result = await db.command('ping')
    print(result)
asyncio.run(test())
"
```

**Solutions**:

- Verify connection string format
- Check network connectivity
- Verify authentication credentials
- Check MongoDB Atlas IP whitelist

#### 4. High Memory Usage

**Problem**: Application consuming too much memory

**Diagnosis**:

```bash
# Check container memory usage
docker stats

# Check Python memory usage
docker-compose exec backend python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

**Solutions**:

- Increase container memory limits
- Optimize database queries
- Implement connection pooling
- Add memory monitoring alerts

### Log Analysis

#### 1. Backend Logs

```bash
# View real-time logs
docker-compose logs -f backend

# Filter by log level
docker-compose logs backend | grep "ERROR"

# Search for specific call
docker-compose logs backend | grep "call_abc123"
```

#### 2. Frontend Logs

```bash
# View frontend logs
docker-compose logs -f frontend

# Check browser console for client-side errors
# Open browser dev tools -> Console tab
```

#### 3. Database Logs

```bash
# MongoDB logs (if self-hosted)
sudo tail -f /var/log/mongodb/mongod.log

# Check slow queries
mongosh
db.setProfilingLevel(2, { slowms: 100 })
db.system.profile.find().sort({ ts: -1 }).limit(5)
```

## Maintenance

### Regular Maintenance Tasks

#### 1. Database Maintenance

```bash
# Weekly database cleanup (run as cron job)
#!/bin/bash
# cleanup_old_data.sh

# Delete old call recordings (>90 days)
mongosh "$MONGODB_URI" --eval "
db.calls.updateMany(
  { created_at: { \$lt: new Date(Date.now() - 90*24*60*60*1000) } },
  { \$unset: { recording_url: 1, transcript_url: 1 } }
)"

# Delete old conversation turns (>30 days)
mongosh "$MONGODB_URI" --eval "
db.conversations.updateMany(
  {},
  { \$pull: { turns: { timestamp: { \$lt: new Date(Date.now() - 30*24*60*60*1000) } } } }
)"
```

#### 2. Log Rotation

```bash
# Configure logrotate
sudo tee /etc/logrotate.d/voice-agent << EOF
/var/log/voice-agent/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 www-data www-data
    postrotate
        docker-compose restart backend
    endscript
}
EOF
```

#### 3. Security Updates

```bash
# Monthly security updates
#!/bin/bash
# security_update.sh

# Update base images
docker-compose pull
docker-compose up -d

# Update Python dependencies
cd backend
pip list --outdated
pip install -U package_name

# Update Node.js dependencies
cd frontend
npm audit
npm update
```

#### 4. Backup Procedures

```bash
# Daily MongoDB backup
#!/bin/bash
# backup_mongodb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"

# Create backup
mongodump --uri="$MONGODB_URI" --out="$BACKUP_DIR/backup_$DATE"

# Compress backup
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" -C "$BACKUP_DIR" "backup_$DATE"
rm -rf "$BACKUP_DIR/backup_$DATE"

# Upload to cloud storage (optional)
aws s3 cp "$BACKUP_DIR/backup_$DATE.tar.gz" s3://your-backup-bucket/mongodb/

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete
```

### Performance Optimization

#### 1. Database Optimization

```javascript
// Create compound indexes for common queries
db.leads.createIndex({ status: 1, created_at: -1 });
db.leads.createIndex({ phone: 1, status: 1 });
db.calls.createIndex({ lead_id: 1, status: 1, created_at: -1 });

// Analyze query performance
db.leads.find({ status: "qualified" }).explain("executionStats");
```

#### 2. Application Optimization

```python
# Enable connection pooling
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    mongodb_uri,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000
)
```

#### 3. Caching Strategy

```python
# Implement Redis caching for prompts
import redis
import json

redis_client = redis.Redis(host='redis', port=6379, db=0)

async def get_cached_prompt(prompt_id: str):
    cached = redis_client.get(f"prompt:{prompt_id}")
    if cached:
        return json.loads(cached)

    # Fetch from database and cache
    prompt = await fetch_prompt_from_db(prompt_id)
    redis_client.setex(f"prompt:{prompt_id}", 3600, json.dumps(prompt))
    return prompt
```

### Scaling Considerations

#### 1. Horizontal Scaling

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-deployment
  minReplicas: 2
  maxReplicas: 10
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
```

#### 2. Load Balancing

```nginx
# nginx load balancer configuration
upstream backend_servers {
    least_conn;
    server backend-1:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;
    server backend-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

This deployment guide provides comprehensive instructions for setting up the AI Voice Loan Agent in both development and production environments, with detailed configuration, monitoring, and maintenance procedures.

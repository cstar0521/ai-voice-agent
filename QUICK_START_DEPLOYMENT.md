# Quick Start Deployment Guide

Get the AI Voice Loan Agent up and running in minutes.

## Prerequisites

- Docker and Docker Compose installed
- OR Kubernetes cluster with kubectl configured
- Environment variables configured

## Option 1: Local Development (Docker Compose)

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd AI-Calling

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Initialize Database

```bash
# Run database initialization
docker-compose exec backend python -m app.init_db

# Seed sample data (optional)
docker-compose exec backend python seed_data.py
```

### 5. Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Option 2: Kubernetes Deployment

### 1. Build and Push Images

```bash
# Build images
docker build -t your-registry/voice-agent-backend:v1.0.0 ./backend
docker build -t your-registry/voice-agent-frontend:v1.0.0 ./frontend

# Push to registry
docker push your-registry/voice-agent-backend:v1.0.0
docker push your-registry/voice-agent-frontend:v1.0.0
```

### 2. Update Configuration

```bash
# Update image references
cd k8s
sed -i 's|your-registry|your-actual-registry|g' *-deployment.yaml

# Update domain names
sed -i 's|yourdomain.com|your-actual-domain.com|g' configmap.yaml ingress.yaml

# Update secrets (IMPORTANT!)
nano secrets.yaml
# Replace all placeholder values with actual credentials
```

### 3. Deploy to Kubernetes

```bash
# Deploy using script
./deploy.sh production

# Or manually
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f mongodb-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n voice-agent

# Check services
kubectl get svc -n voice-agent

# Check ingress
kubectl get ingress -n voice-agent

# View logs
kubectl logs -f deployment/backend -n voice-agent
```

### 5. Access Application

```bash
# Port forward for local access
kubectl port-forward svc/frontend-service 3000:3000 -n voice-agent
kubectl port-forward svc/backend-service 8000:8000 -n voice-agent

# Or access via ingress (if configured)
# https://yourdomain.com
# https://api.yourdomain.com
```

## Option 3: CI/CD Deployment

### 1. Configure GitHub

```bash
# Add secrets to GitHub repository
# Settings > Secrets and variables > Actions

# Required secrets:
# - KUBE_CONFIG_STAGING (base64 encoded kubeconfig)
# - KUBE_CONFIG_PRODUCTION (base64 encoded kubeconfig)
# - SLACK_WEBHOOK (optional, for notifications)
```

### 2. Create Environments

```bash
# In GitHub repository settings:
# Settings > Environments

# Create:
# - staging (no protection)
# - production-approval (required reviewers)
# - production (required reviewers)
```

### 3. Deploy to Staging

```bash
# Push to develop branch
git checkout develop
git merge feature-branch
git push origin develop

# Automatically deploys to staging
# Monitor: gh run watch
```

### 4. Deploy to Production

```bash
# Create release tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Create GitHub release
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes"

# Approve deployment in GitHub UI
# Actions > Deploy to Production > Review deployments > Approve

# Monitor deployment
gh run watch
```

## Environment Variables

### Required Variables

```bash
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxx...
TWILIO_AUTH_TOKEN=xxxxx...
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI
OPENAI_API_KEY=sk-xxxxx...

# Security
JWT_SECRET_KEY=your-secret-key-min-32-chars

# Optional: Sarvam AI (for Indian languages)
SARVAM_API_KEY=your-sarvam-key
SPEECH_PROVIDER=sarvam_ai
```

### Optional Variables

```bash
# Notifications
SUPRSEND_API_KEY=your-suprsend-key
GUPSHUP_API_KEY=your-gupshup-key

# Database (if using external MongoDB)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/voice_agent

# Frontend
REACT_APP_API_URL=https://api.yourdomain.com
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check environment variables
docker-compose exec backend env | grep TWILIO

# Restart services
docker-compose restart backend
```

### Database Connection Issues

```bash
# Check MongoDB is running
docker-compose ps mongo

# Test connection
docker-compose exec backend python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('OK')"

# Check MongoDB logs
docker-compose logs mongo
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000
lsof -i :3000

# Kill process or change port in docker-compose.yml
```

### Kubernetes Pods Not Starting

```bash
# Check pod status
kubectl get pods -n voice-agent

# Describe pod for events
kubectl describe pod <pod-name> -n voice-agent

# Check logs
kubectl logs <pod-name> -n voice-agent

# Check previous logs if crashed
kubectl logs <pod-name> -n voice-agent --previous
```

### Image Pull Errors

```bash
# Verify image exists
docker pull your-registry/voice-agent-backend:v1.0.0

# Check registry credentials
kubectl get secret -n voice-agent

# Create image pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=your-registry \
  --docker-username=your-username \
  --docker-password=your-password \
  -n voice-agent
```

## Health Checks

### Backend Health

```bash
# Docker Compose
curl http://localhost:8000/health

# Kubernetes
kubectl port-forward svc/backend-service 8000:8000 -n voice-agent
curl http://localhost:8000/health
```

### Frontend Health

```bash
# Docker Compose
curl http://localhost:3000/health

# Kubernetes
kubectl port-forward svc/frontend-service 3000:3000 -n voice-agent
curl http://localhost:3000/health
```

### Database Health

```bash
# Docker Compose
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"

# Kubernetes
kubectl exec -it deployment/mongo -n voice-agent -- mongosh --eval "db.adminCommand('ping')"
```

## Testing

### Run Tests Locally

```bash
# Backend tests
cd backend
pip install -r requirements.txt
pytest

# Frontend tests
cd frontend
npm install
npm test
```

### Run Tests in Docker

```bash
# Backend
docker-compose exec backend pytest

# Frontend
docker-compose exec frontend npm test
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:3000
curl http://localhost:8000/api/v1/config/prompts
```

## Next Steps

After successful deployment:

1. **Configure Monitoring**
   - Set up Prometheus and Grafana
   - Configure alerts

2. **Set Up Logging**
   - Configure log aggregation (ELK, Loki)
   - Set up log retention policies

3. **Configure Backups**
   - Set up automated database backups
   - Test restore procedures

4. **Security Hardening**
   - Enable network policies
   - Configure RBAC
   - Set up WAF

5. **Performance Optimization**
   - Configure caching
   - Optimize resource limits
   - Set up CDN

## Documentation

For detailed information, see:

- `DOCKER_DEPLOYMENT.md` - Docker deployment guide
- `KUBERNETES_DEPLOYMENT.md` - Kubernetes deployment guide
- `CI_CD_GUIDE.md` - CI/CD pipeline guide
- `DEPLOYMENT_SUMMARY.md` - Complete deployment summary

## Support

For issues:

1. Check logs: `docker-compose logs -f` or `kubectl logs -f deployment/backend -n voice-agent`
2. Verify configuration: Check environment variables and secrets
3. Review documentation: See guides above
4. Check GitHub Actions: `gh run list` and `gh run view <run-id> --log`

## Quick Commands Reference

```bash
# Docker Compose
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs -f backend    # View logs
docker-compose ps                 # Check status
docker-compose restart backend    # Restart service

# Kubernetes
kubectl get pods -n voice-agent                    # List pods
kubectl logs -f deployment/backend -n voice-agent  # View logs
kubectl describe pod <pod> -n voice-agent          # Pod details
kubectl exec -it <pod> -n voice-agent -- sh        # Shell access
kubectl port-forward svc/backend-service 8000:8000 # Port forward

# GitHub CLI
gh run list                       # List workflow runs
gh run watch                      # Watch current run
gh run view <run-id> --log        # View logs
gh workflow run <workflow>.yml    # Trigger workflow
```

## Success!

If you can access the application and see the health checks responding, you're all set! 🎉

- Frontend: ✅ http://localhost:3000
- Backend: ✅ http://localhost:8000
- API Docs: ✅ http://localhost:8000/docs

Happy deploying! 🚀

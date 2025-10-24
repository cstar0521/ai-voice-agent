# Kubernetes Deployment Guide

This guide covers deploying the AI Voice Loan Agent to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured to access your cluster
- Container registry (Docker Hub, GCR, ECR, etc.)
- At least 4GB RAM and 2 CPU cores available
- Ingress controller installed (NGINX recommended)
- Optional: Helm 3+ for package management

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Ingress Controller                 │
│              (nginx/traefik/cloud LB)               │
└────────────┬────────────────────────┬────────────────┘
             │                        │
    ┌────────▼────────┐      ┌───────▼────────┐
    │   Frontend      │      │    Backend     │
    │   Service       │      │    Service     │
    │   (2-5 pods)    │      │   (2-10 pods)  │
    └─────────────────┘      └────────┬───────┘
                                      │
                             ┌────────▼────────┐
                             │    MongoDB      │
                             │    Service      │
                             │    (1 pod)      │
                             └─────────────────┘
```

## Quick Start

### 1. Build and Push Docker Images

```bash
# Build backend image
cd backend
docker build -t your-registry/voice-agent-backend:v1.0.0 .
docker push your-registry/voice-agent-backend:v1.0.0

# Build frontend image
cd ../frontend
docker build -t your-registry/voice-agent-frontend:v1.0.0 .
docker push your-registry/voice-agent-frontend:v1.0.0
```

### 2. Update Configuration

Edit `k8s/configmap.yaml`:

```yaml
data:
  REACT_APP_API_URL: "https://api.yourdomain.com" # Your actual domain
```

Edit `k8s/secrets.yaml` with your actual credentials:

```bash
# Generate base64 encoded values
echo -n "your-actual-value" | base64
```

Update image references in deployment files:

- `k8s/backend-deployment.yaml`: Update `image:` field
- `k8s/frontend-deployment.yaml`: Update `image:` field

### 3. Deploy to Kubernetes

```bash
cd k8s
./deploy.sh production
```

Or manually:

```bash
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
# Check all resources
kubectl get all -n voice-agent

# Check pod status
kubectl get pods -n voice-agent

# Check logs
kubectl logs -f deployment/backend -n voice-agent
kubectl logs -f deployment/frontend -n voice-agent
```

## Configuration Details

### ConfigMap

The ConfigMap stores non-sensitive configuration:

- Environment settings
- API URLs
- Feature flags
- Service endpoints

Edit `k8s/configmap.yaml` to customize.

### Secrets

**IMPORTANT**: Never commit real secrets to version control!

For production, use one of these approaches:

#### Option 1: Sealed Secrets

```bash
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret
kubeseal --format=yaml < secrets.yaml > sealed-secrets.yaml
kubectl apply -f sealed-secrets.yaml
```

#### Option 2: External Secrets Operator

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace

# Configure with your secret provider (AWS, GCP, Azure, Vault)
```

#### Option 3: Cloud Provider Secret Manager

- AWS: Use AWS Secrets Manager + IRSA
- GCP: Use Secret Manager + Workload Identity
- Azure: Use Key Vault + Pod Identity

### Persistent Storage

MongoDB uses a PersistentVolumeClaim (PVC) for data storage.

**For production**, use:

- Managed database service (MongoDB Atlas, AWS DocumentDB)
- Or configure proper storage class:

```yaml
# In mongodb-deployment.yaml
spec:
  storageClassName: fast-ssd # Your storage class
  resources:
    requests:
      storage: 50Gi # Adjust based on needs
```

## Ingress Configuration

### NGINX Ingress Controller

Install if not already present:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### SSL/TLS with Cert-Manager

Install Cert-Manager:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

Create ClusterIssuer:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

Update `k8s/ingress.yaml`:

```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

## Horizontal Pod Autoscaling

The HPA automatically scales pods based on CPU and memory usage.

View HPA status:

```bash
kubectl get hpa -n voice-agent
```

Adjust scaling parameters in `k8s/hpa.yaml`:

```yaml
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          averageUtilization: 70 # Scale when CPU > 70%
```

## Monitoring and Logging

### View Logs

```bash
# Stream logs from all backend pods
kubectl logs -f deployment/backend -n voice-agent

# View logs from specific pod
kubectl logs pod-name -n voice-agent

# View previous container logs (if crashed)
kubectl logs pod-name -n voice-agent --previous
```

### Resource Usage

```bash
# View resource usage
kubectl top pods -n voice-agent
kubectl top nodes

# Describe pod for events
kubectl describe pod pod-name -n voice-agent
```

### Prometheus & Grafana (Optional)

Install monitoring stack:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

## Maintenance Operations

### Update Application

```bash
# Build new image
docker build -t your-registry/voice-agent-backend:v1.1.0 .
docker push your-registry/voice-agent-backend:v1.1.0

# Update deployment
kubectl set image deployment/backend \
  backend=your-registry/voice-agent-backend:v1.1.0 \
  -n voice-agent

# Check rollout status
kubectl rollout status deployment/backend -n voice-agent
```

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment/backend -n voice-agent

# Rollback to previous version
kubectl rollout undo deployment/backend -n voice-agent

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n voice-agent
```

### Scale Manually

```bash
# Scale backend
kubectl scale deployment/backend --replicas=5 -n voice-agent

# Scale frontend
kubectl scale deployment/frontend --replicas=3 -n voice-agent
```

### Database Backup

```bash
# Create backup
kubectl exec -it deployment/mongo -n voice-agent -- \
  mongodump --out=/tmp/backup

# Copy backup to local
kubectl cp voice-agent/mongo-pod:/tmp/backup ./backup

# Restore backup
kubectl cp ./backup voice-agent/mongo-pod:/tmp/backup
kubectl exec -it deployment/mongo -n voice-agent -- \
  mongorestore /tmp/backup
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n voice-agent

# Describe pod for events
kubectl describe pod pod-name -n voice-agent

# Check logs
kubectl logs pod-name -n voice-agent
```

Common issues:

- Image pull errors: Check registry credentials
- CrashLoopBackOff: Check application logs
- Pending: Check resource availability

### Service Not Accessible

```bash
# Check service
kubectl get svc -n voice-agent

# Check endpoints
kubectl get endpoints -n voice-agent

# Test service internally
kubectl run -it --rm debug --image=busybox --restart=Never -n voice-agent -- \
  wget -O- http://backend-service:8000/health
```

### Ingress Issues

```bash
# Check ingress
kubectl get ingress -n voice-agent
kubectl describe ingress voice-agent-ingress -n voice-agent

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### Database Connection Issues

```bash
# Check MongoDB status
kubectl get pods -l app=mongo -n voice-agent

# Test MongoDB connection
kubectl exec -it deployment/backend -n voice-agent -- \
  python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('OK')"

# Check MongoDB logs
kubectl logs deployment/mongo -n voice-agent
```

## Security Best Practices

1. **Use RBAC**: Create service accounts with minimal permissions
2. **Network Policies**: Restrict pod-to-pod communication
3. **Pod Security Standards**: Enforce security contexts
4. **Secrets Management**: Use external secret managers
5. **Image Scanning**: Scan images for vulnerabilities
6. **Regular Updates**: Keep Kubernetes and images updated

### Example Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: voice-agent
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: mongo
      ports:
        - protocol: TCP
          port: 27017
```

## Production Checklist

- [ ] Use managed MongoDB (MongoDB Atlas) instead of in-cluster
- [ ] Configure proper resource limits and requests
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation (ELK, Loki, CloudWatch)
- [ ] Enable SSL/TLS with valid certificates
- [ ] Use external secrets management
- [ ] Configure backup and disaster recovery
- [ ] Set up CI/CD pipeline
- [ ] Implement network policies
- [ ] Configure pod disruption budgets
- [ ] Set up health checks and readiness probes
- [ ] Use multiple availability zones
- [ ] Configure autoscaling based on metrics
- [ ] Implement rate limiting at ingress level
- [ ] Set up WAF (Web Application Firewall)

## Cost Optimization

1. **Right-size resources**: Monitor and adjust CPU/memory limits
2. **Use spot instances**: For non-critical workloads
3. **Cluster autoscaling**: Scale nodes based on demand
4. **Resource quotas**: Prevent resource waste
5. **Managed services**: Use cloud provider managed databases

## Support and Resources

- Kubernetes Documentation: https://kubernetes.io/docs/
- NGINX Ingress: https://kubernetes.github.io/ingress-nginx/
- Cert-Manager: https://cert-manager.io/docs/
- Helm Charts: https://helm.sh/docs/

For issues:

1. Check pod logs: `kubectl logs -f deployment/backend -n voice-agent`
2. Check events: `kubectl get events -n voice-agent --sort-by='.lastTimestamp'`
3. Verify configuration: `kubectl get configmap,secret -n voice-agent`

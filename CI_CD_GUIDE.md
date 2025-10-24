# CI/CD Pipeline Guide

This guide covers the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the AI Voice Loan Agent.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and consists of:

1. **Continuous Integration (CI)**: Automated testing and validation
2. **Docker Image Building**: Building and pushing container images
3. **Staging Deployment**: Automatic deployment to staging environment
4. **Production Deployment**: Manual approval-based deployment to production

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Code Push/PR                             │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │   CI Pipeline   │
    │  - Lint         │
    │  - Test         │
    │  - Security     │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Build Docker   │
    │    Images       │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Deploy to      │
    │   Staging       │
    │  (automatic)    │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Manual         │
    │  Approval       │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  Deploy to      │
    │  Production     │
    └─────────────────┘
```

## Workflows

### 1. Backend CI (`backend-ci.yml`)

**Triggers:**

- Push to `main` or `develop` branches (backend changes)
- Pull requests to `main` or `develop` (backend changes)

**Steps:**

1. Set up Python 3.10 environment
2. Install dependencies
3. Run linting (flake8)
4. Run tests with coverage (pytest)
5. Run security scan (Bandit)
6. Upload coverage reports to Codecov

**Required Secrets:** None (uses MongoDB service container)

### 2. Frontend CI (`frontend-ci.yml`)

**Triggers:**

- Push to `main` or `develop` branches (frontend changes)
- Pull requests to `main` or `develop` (frontend changes)

**Steps:**

1. Set up Node.js 18 environment
2. Install dependencies
3. Run linting
4. Run tests with coverage
5. Build production bundle
6. Upload coverage reports to Codecov

**Required Secrets:** None

### 3. Docker Build (`docker-build.yml`)

**Triggers:**

- Push to `main` branch
- Version tags (e.g., `v1.0.0`)
- Manual workflow dispatch

**Steps:**

1. Build backend Docker image
2. Build frontend Docker image
3. Push images to GitHub Container Registry
4. Scan images for vulnerabilities (Trivy)
5. Upload security scan results

**Required Secrets:**

- `GITHUB_TOKEN` (automatically provided)

**Image Tags:**

- `latest` - Latest main branch build
- `v1.0.0` - Semantic version tags
- `main-abc123` - Branch name + commit SHA

### 4. Deploy to Staging (`deploy-staging.yml`)

**Triggers:**

- Push to `develop` branch
- Manual workflow dispatch

**Steps:**

1. Configure kubectl with staging cluster
2. Update image tags to latest commit SHA
3. Apply Kubernetes manifests
4. Wait for rollout completion
5. Run smoke tests
6. Send Slack notification

**Required Secrets:**

- `KUBE_CONFIG_STAGING` - Base64 encoded kubeconfig for staging cluster
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

**Environment:** `staging`

### 5. Deploy to Production (`deploy-production.yml`)

**Triggers:**

- Release published
- Manual workflow dispatch with version input

**Steps:**

1. **Manual approval required** (GitHub Environment protection)
2. Configure kubectl with production cluster
3. Create backup of current deployment
4. Update image tags to release version
5. Apply Kubernetes manifests with rolling update
6. Wait for rollout completion
7. Run comprehensive smoke tests
8. **Rollback automatically on failure**
9. Send Slack notification
10. Create deployment record

**Required Secrets:**

- `KUBE_CONFIG_PRODUCTION` - Base64 encoded kubeconfig for production cluster
- `SLACK_WEBHOOK` - Slack webhook URL for notifications

**Environment:** `production` (with approval required)

## Setup Instructions

### 1. Configure GitHub Secrets

Navigate to: `Settings > Secrets and variables > Actions`

Add the following secrets:

#### For Staging Deployment:

```bash
# Generate kubeconfig for staging
kubectl config view --flatten --minify > staging-kubeconfig.yaml

# Base64 encode it
cat staging-kubeconfig.yaml | base64 > staging-kubeconfig-base64.txt

# Add as secret: KUBE_CONFIG_STAGING
```

#### For Production Deployment:

```bash
# Generate kubeconfig for production
kubectl config view --flatten --minify > production-kubeconfig.yaml

# Base64 encode it
cat production-kubeconfig.yaml | base64 > production-kubeconfig-base64.txt

# Add as secret: KUBE_CONFIG_PRODUCTION
```

#### For Notifications:

```bash
# Slack webhook URL
# Add as secret: SLACK_WEBHOOK
```

### 2. Configure GitHub Environments

Navigate to: `Settings > Environments`

#### Create Staging Environment:

- Name: `staging`
- URL: `https://staging.yourdomain.com`
- No protection rules needed (auto-deploy)

#### Create Production Environment:

- Name: `production`
- URL: `https://yourdomain.com`
- Protection rules:
  - ✅ Required reviewers (add team members)
  - ✅ Wait timer: 5 minutes (optional)
  - ✅ Deployment branches: Only `main` and tags

#### Create Production Approval Environment:

- Name: `production-approval`
- Protection rules:
  - ✅ Required reviewers (add approvers)

### 3. Configure Container Registry

The pipeline uses GitHub Container Registry (ghcr.io) by default.

**Alternative registries:**

#### Docker Hub:

```yaml
env:
  REGISTRY: docker.io
  IMAGE_NAME_BACKEND: your-username/voice-agent-backend
```

Add secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

#### AWS ECR:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1

- name: Login to Amazon ECR
  uses: aws-actions/amazon-ecr-login@v2
```

#### Google Container Registry:

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_CREDENTIALS }}

- name: Configure Docker for GCR
  run: gcloud auth configure-docker
```

## Usage

### Running CI Tests

CI runs automatically on every push and pull request. To run locally:

**Backend:**

```bash
cd backend
pip install -r requirements.txt
pytest --cov=app
flake8 .
bandit -r app/
```

**Frontend:**

```bash
cd frontend
npm install
npm test
npm run build
```

### Building Docker Images

Images are built automatically on push to `main`. To build manually:

```bash
# Trigger manual build
gh workflow run docker-build.yml
```

Or build locally:

```bash
docker build -t voice-agent-backend:local ./backend
docker build -t voice-agent-frontend:local ./frontend
```

### Deploying to Staging

Staging deploys automatically when you push to `develop`:

```bash
git checkout develop
git merge feature-branch
git push origin develop
```

Or trigger manually:

```bash
gh workflow run deploy-staging.yml
```

### Deploying to Production

#### Method 1: Create a Release (Recommended)

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Create release on GitHub
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes here"
```

This will:

1. Trigger the production deployment workflow
2. Require manual approval
3. Deploy the tagged version

#### Method 2: Manual Workflow Dispatch

```bash
gh workflow run deploy-production.yml -f version=v1.0.0
```

Or via GitHub UI:

1. Go to Actions tab
2. Select "Deploy to Production"
3. Click "Run workflow"
4. Enter version tag
5. Approve deployment when prompted

### Monitoring Deployments

**View workflow runs:**

```bash
gh run list --workflow=deploy-production.yml
```

**View specific run:**

```bash
gh run view <run-id>
```

**View logs:**

```bash
gh run view <run-id> --log
```

**In GitHub UI:**

1. Go to Actions tab
2. Select workflow
3. Click on specific run
4. View logs and status

## Rollback Procedures

### Automatic Rollback

Production deployment automatically rolls back if:

- Smoke tests fail
- Deployment verification fails
- Any step in the deployment fails

### Manual Rollback

#### Option 1: Redeploy Previous Version

```bash
# Find previous successful version
gh release list

# Deploy previous version
gh workflow run deploy-production.yml -f version=v1.0.0
```

#### Option 2: Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/backend -n voice-agent

# Rollback to previous version
kubectl rollout undo deployment/backend -n voice-agent
kubectl rollout undo deployment/frontend -n voice-agent
```

#### Option 3: Use Backup Artifacts

```bash
# Download backup from failed deployment
gh run download <run-id>

# Apply backup
kubectl apply -f backup-backend-deployment.yaml
kubectl apply -f backup-frontend-deployment.yaml
```

## Troubleshooting

### CI Tests Failing

**Check logs:**

```bash
gh run view <run-id> --log
```

**Common issues:**

- Dependency conflicts: Update `requirements.txt` or `package.json`
- Test failures: Fix failing tests
- Linting errors: Run `flake8` or `npm run lint` locally

### Docker Build Failing

**Check build logs:**

```bash
gh run view <run-id> --log
```

**Common issues:**

- Dockerfile syntax errors
- Missing dependencies
- Build context too large (add to `.dockerignore`)

### Deployment Failing

**Check deployment logs:**

```bash
kubectl logs -f deployment/backend -n voice-agent
kubectl describe pod <pod-name> -n voice-agent
```

**Common issues:**

- Image pull errors: Check registry credentials
- Configuration errors: Verify ConfigMap and Secrets
- Resource limits: Check cluster capacity
- Health check failures: Verify application is starting correctly

### Rollback Not Working

**Manual intervention:**

```bash
# Scale down new deployment
kubectl scale deployment/backend --replicas=0 -n voice-agent

# Apply previous deployment
kubectl apply -f backup-backend-deployment.yaml

# Verify
kubectl get pods -n voice-agent
```

## Best Practices

### 1. Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for staging
- `feature/*` - Feature branches
- `hotfix/*` - Emergency fixes

### 2. Versioning

Use Semantic Versioning (SemVer):

- `v1.0.0` - Major.Minor.Patch
- `v1.1.0` - New features (backward compatible)
- `v1.0.1` - Bug fixes
- `v2.0.0` - Breaking changes

### 3. Commit Messages

Follow Conventional Commits:

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
chore: update dependencies
```

### 4. Pull Request Workflow

1. Create feature branch
2. Make changes
3. Run tests locally
4. Create pull request
5. Wait for CI to pass
6. Request review
7. Merge to develop
8. Test in staging
9. Merge to main
10. Create release

### 5. Testing Strategy

- Unit tests: Test individual components
- Integration tests: Test component interactions
- Smoke tests: Verify basic functionality after deployment
- Load tests: Test performance under load (separate workflow)

### 6. Security

- Scan dependencies regularly
- Use Dependabot for automated updates
- Scan Docker images for vulnerabilities
- Rotate secrets periodically
- Use least privilege for service accounts

## Monitoring and Alerts

### GitHub Actions Notifications

Configure notifications in GitHub:

1. Settings > Notifications
2. Enable "Actions" notifications
3. Choose email or mobile

### Slack Integration

The pipeline sends notifications to Slack:

- ✅ Successful deployments
- ❌ Failed deployments
- ⚠️ Rollbacks

### Monitoring Deployments

Use Kubernetes monitoring:

```bash
# Watch deployment status
kubectl get pods -n voice-agent -w

# View events
kubectl get events -n voice-agent --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n voice-agent
```

## Cost Optimization

### GitHub Actions Minutes

- Free tier: 2,000 minutes/month
- Optimize workflows:
  - Use caching for dependencies
  - Run tests in parallel
  - Skip unnecessary steps

### Container Registry Storage

- Clean up old images regularly
- Use image retention policies
- Consider external registry for large images

## Support and Resources

- GitHub Actions Documentation: https://docs.github.com/en/actions
- Kubernetes Documentation: https://kubernetes.io/docs/
- Docker Documentation: https://docs.docker.com/

For issues:

1. Check workflow logs
2. Verify secrets and configuration
3. Test locally before pushing
4. Review recent changes

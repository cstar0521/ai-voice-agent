# GitHub Actions Workflows

This directory contains CI/CD workflows for the AI Voice Loan Agent project.

## Workflows Overview

### Continuous Integration

| Workflow              | Trigger                                    | Purpose                                         |
| --------------------- | ------------------------------------------ | ----------------------------------------------- |
| `backend-ci.yml`      | Push/PR to main/develop (backend changes)  | Run backend tests, linting, and security scans  |
| `frontend-ci.yml`     | Push/PR to main/develop (frontend changes) | Run frontend tests, linting, and build          |
| `scheduled-tests.yml` | Daily at 2 AM UTC                          | Run comprehensive test suite and security scans |

### Continuous Deployment

| Workflow                | Trigger                    | Purpose                                     |
| ----------------------- | -------------------------- | ------------------------------------------- |
| `docker-build.yml`      | Push to main, version tags | Build and push Docker images to registry    |
| `deploy-staging.yml`    | Push to develop            | Automatically deploy to staging environment |
| `deploy-production.yml` | Release published, manual  | Deploy to production with approval          |

### Dependency Management

| File             | Purpose                                                                  |
| ---------------- | ------------------------------------------------------------------------ |
| `dependabot.yml` | Automated dependency updates for Python, npm, Docker, and GitHub Actions |

## Quick Reference

### Running Workflows Manually

```bash
# Trigger any workflow
gh workflow run <workflow-name>.yml

# Examples
gh workflow run docker-build.yml
gh workflow run deploy-staging.yml
gh workflow run deploy-production.yml -f version=v1.0.0
```

### Viewing Workflow Status

```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log

# Watch a running workflow
gh run watch
```

### Required Secrets

Configure these in: `Settings > Secrets and variables > Actions`

| Secret                   | Description                              | Used By                  |
| ------------------------ | ---------------------------------------- | ------------------------ |
| `KUBE_CONFIG_STAGING`    | Base64 encoded kubeconfig for staging    | deploy-staging.yml       |
| `KUBE_CONFIG_PRODUCTION` | Base64 encoded kubeconfig for production | deploy-production.yml    |
| `SLACK_WEBHOOK`          | Slack webhook URL for notifications      | All deployment workflows |
| `GITHUB_TOKEN`           | Automatically provided by GitHub         | docker-build.yml         |

### Required Environments

Configure these in: `Settings > Environments`

| Environment           | Protection Rules                        | URL                            |
| --------------------- | --------------------------------------- | ------------------------------ |
| `staging`             | None (auto-deploy)                      | https://staging.yourdomain.com |
| `production-approval` | Required reviewers                      | -                              |
| `production`          | Required reviewers, deployment branches | https://yourdomain.com         |

## Workflow Details

### Backend CI

- Runs on: Ubuntu latest
- Python version: 3.10
- Services: MongoDB 6.0
- Steps: Install deps → Lint → Test → Security scan
- Coverage: Uploaded to Codecov

### Frontend CI

- Runs on: Ubuntu latest
- Node version: 18
- Steps: Install deps → Lint → Test → Build
- Coverage: Uploaded to Codecov
- Artifacts: Build output (7 days retention)

### Docker Build

- Runs on: Ubuntu latest
- Registry: GitHub Container Registry (ghcr.io)
- Images: backend, frontend
- Tags: latest, version tags, branch-sha
- Security: Trivy vulnerability scanning

### Deploy Staging

- Runs on: Ubuntu latest
- Environment: staging
- Steps: Update images → Deploy → Verify → Smoke tests
- Notifications: Slack on success/failure

### Deploy Production

- Runs on: Ubuntu latest
- Environment: production (requires approval)
- Steps: Backup → Update images → Deploy → Verify → Smoke tests
- Rollback: Automatic on failure
- Notifications: Slack on success/failure

### Scheduled Tests

- Runs on: Daily at 2 AM UTC
- Tests: Backend, Frontend, Integration, Security
- Notifications: Slack on failure only

## Customization

### Change Triggers

Edit the `on:` section in workflow files:

```yaml
on:
  push:
    branches: [main, develop, feature/*]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 2 * * *" # Daily at 2 AM UTC
  workflow_dispatch: # Manual trigger
```

### Change Test Commands

Edit the test steps:

```yaml
- name: Run tests
  run: |
    pytest -v --cov=app
    # Add more test commands
```

### Change Deployment Strategy

Edit deployment steps in `deploy-*.yml`:

```yaml
- name: Deploy to Kubernetes
  run: |
    kubectl apply -f k8s/
    kubectl rollout status deployment/backend
```

### Add New Workflows

Create new workflow file in `.github/workflows/`:

```yaml
name: My Custom Workflow

on:
  push:
    branches: [main]

jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run custom script
        run: ./scripts/my-script.sh
```

## Troubleshooting

### Workflow Not Triggering

1. Check trigger conditions (branches, paths)
2. Verify workflow file syntax (YAML)
3. Check repository settings (Actions enabled)

### Tests Failing

1. View logs: `gh run view <run-id> --log`
2. Run tests locally to reproduce
3. Check for environment-specific issues

### Deployment Failing

1. Check Kubernetes cluster connectivity
2. Verify secrets are configured correctly
3. Check image availability in registry
4. Review deployment logs in Kubernetes

### Secrets Not Working

1. Verify secret names match exactly
2. Check environment configuration
3. Ensure secrets are available in the environment

## Best Practices

1. **Always test locally** before pushing
2. **Use pull requests** for code review
3. **Tag releases** with semantic versioning
4. **Monitor workflow runs** regularly
5. **Keep dependencies updated** (Dependabot)
6. **Review security scans** and fix vulnerabilities
7. **Use caching** to speed up workflows
8. **Limit workflow runs** to save minutes

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [CI/CD Guide](../CI_CD_GUIDE.md)

## Support

For issues or questions:

1. Check workflow logs
2. Review this documentation
3. Consult the CI/CD Guide
4. Contact the DevOps team

# Docker Deployment Guide

This guide covers deploying the AI Voice Loan Agent using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- Ports 3000, 8000, and 27017 available

## Quick Start (Development)

1. **Copy environment variables:**

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   - Twilio credentials
   - OpenAI API key
   - Sarvam AI API key (if using)
   - JWT secret key (generate a secure random string)

3. **Start all services:**

   ```bash
   docker-compose up -d
   ```

4. **View logs:**

   ```bash
   docker-compose logs -f
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

6. **Stop services:**
   ```bash
   docker-compose down
   ```

## Production Deployment

1. **Use production compose file:**

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Set production environment variables:**
   - Use external MongoDB (MongoDB Atlas recommended)
   - Set `MONGODB_URI` to your production database
   - Use strong JWT secret keys
   - Configure proper API keys for all services

3. **Enable SSL/TLS:**
   - Use a reverse proxy (nginx, Traefik, or cloud load balancer)
   - Configure SSL certificates (Let's Encrypt recommended)

## Service Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│   MongoDB   │
│  (Port 3000)│     │  (Port 8000)│     │ (Port 27017)│
└─────────────┘     └─────────────┘     └─────────────┘
```

## Environment Variables

### Required Variables

| Variable              | Description                          | Example           |
| --------------------- | ------------------------------------ | ----------------- |
| `TWILIO_ACCOUNT_SID`  | Twilio account identifier            | `ACxxxxx...`      |
| `TWILIO_AUTH_TOKEN`   | Twilio authentication token          | `xxxxx...`        |
| `TWILIO_PHONE_NUMBER` | Twilio phone number                  | `+1234567890`     |
| `OPENAI_API_KEY`      | OpenAI API key                       | `sk-xxxxx...`     |
| `JWT_SECRET_KEY`      | Secret for JWT tokens (min 32 chars) | `your-secret-key` |

### Optional Variables

| Variable            | Description               | Default                             |
| ------------------- | ------------------------- | ----------------------------------- |
| `SPEECH_PROVIDER`   | Speech service provider   | `sarvam_ai`                         |
| `SARVAM_API_KEY`    | Sarvam AI API key         | -                                   |
| `MONGODB_URI`       | MongoDB connection string | `mongodb://mongo:27017/voice_agent` |
| `REACT_APP_API_URL` | Backend API URL           | `http://localhost:8000`             |

## Docker Commands

### Build images:

```bash
# Development
docker-compose build

# Production
docker-compose -f docker-compose.prod.yml build
```

### Start services:

```bash
# Development (with hot reload)
docker-compose up

# Production (detached)
docker-compose -f docker-compose.prod.yml up -d
```

### View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Execute commands in containers:

```bash
# Backend shell
docker-compose exec backend sh

# Run database migrations
docker-compose exec backend python -m app.init_db

# Run tests
docker-compose exec backend pytest
```

### Stop and remove containers:

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers and volumes (WARNING: deletes data)
docker-compose down -v
```

## Health Checks

All services include health checks:

- **Backend**: `http://localhost:8000/health`
- **Frontend**: `http://localhost:3000/health`
- **MongoDB**: Internal health check via mongosh

Check service health:

```bash
docker-compose ps
```

## Troubleshooting

### Port conflicts:

```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8000
lsof -i :27017

# Change ports in docker-compose.yml if needed
```

### Container won't start:

```bash
# View detailed logs
docker-compose logs backend

# Rebuild without cache
docker-compose build --no-cache backend
```

### Database connection issues:

```bash
# Verify MongoDB is running
docker-compose ps mongo

# Check MongoDB logs
docker-compose logs mongo

# Test connection
docker-compose exec backend python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('OK')"
```

### Permission issues:

```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

## Performance Optimization

### Production optimizations:

1. Use multi-stage builds (already configured)
2. Enable gzip compression (configured in nginx)
3. Use external managed MongoDB (MongoDB Atlas)
4. Configure resource limits in docker-compose:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: "1"
         memory: 1G
   ```

### Monitoring:

```bash
# View resource usage
docker stats

# View container details
docker inspect voice-agent-backend
```

## Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use secrets management** - Consider Docker Secrets or external vaults
3. **Run as non-root user** - Already configured in Dockerfiles
4. **Keep images updated** - Regularly rebuild with latest base images
5. **Scan for vulnerabilities**:
   ```bash
   docker scan voice-agent-backend
   ```

## Backup and Restore

### Backup MongoDB data:

```bash
docker-compose exec mongo mongodump --out=/data/backup
docker cp voice-agent-mongo:/data/backup ./backup
```

### Restore MongoDB data:

```bash
docker cp ./backup voice-agent-mongo:/data/backup
docker-compose exec mongo mongorestore /data/backup
```

## Scaling

For production scaling, consider:

- Kubernetes deployment (see k8s/ directory)
- Load balancer for multiple backend instances
- MongoDB replica set for high availability
- Redis for caching and session management

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Verify environment variables
3. Ensure all required services are running
4. Check network connectivity between containers

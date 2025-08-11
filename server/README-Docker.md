# FuseTester API Server - Docker Deployment

A containerized Node.js HTTP server for receiving and storing fuse monitoring data from the FuseTester Python application.

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed
- Git repository cloned to `/app/fusetester`

### Quick Start

```bash
# Navigate to server directory
cd /app/fusetester/server

# Start the container
docker compose up -d

# Check status
docker compose ps
```

## Container Features

### Base Image
- **Node.js 18 Alpine** - Lightweight, secure base image
- **Non-root user** - Runs as `fusetester` user for security
- **Multi-stage optimized** - Efficient image size

### Data Persistence
- **Database** - SQLite database stored in `./data/fusetester.db`
- **Volume mounting** - Data persists between container restarts
- **Backup friendly** - Database file accessible on host

### Health Checks
- **Built-in health check** - Monitors `/health` endpoint
- **Docker Compose health** - Container restart on failure
- **Logging** - JSON file logging with rotation

## Configuration

### Environment Variables
```yaml
environment:
  - NODE_ENV=production
  - PORT=3000
```

### Port Mapping
- **Container Port**: 3000
- **Host Binding**: 127.0.0.1:3000 (localhost only)
- **Nginx Proxy**: Handles external access

### Database Location
- **Container**: `/app/data/fusetester.db`
- **Host**: `./data/fusetester.db` (relative to server directory)

## Management Commands

### Basic Operations
```bash
# Start container
docker compose up -d

# Stop container
docker compose down

# Restart container
docker compose restart fusetester-api

# View logs
docker compose logs -f fusetester-api

# Check status and health
docker compose ps
```

### Development
```bash
# Build without cache
docker compose build --no-cache

# View real-time logs
docker compose logs -f

# Execute commands in container
docker compose exec fusetester-api sh

# Check container resource usage
docker stats fusetester-api
```

### Updates and Deployment
```bash
# Pull latest code
cd /app/fusetester
git pull origin main

# Rebuild and restart
cd server
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Monitoring

### Health Check
The container includes a built-in health check that:
- Tests the `/health` endpoint every 30 seconds
- Waits 40 seconds for initial startup
- Retries 3 times before marking unhealthy
- Automatically restarts unhealthy containers

### Logging
- **Log Driver**: JSON file
- **Max Size**: 10MB per file
- **Max Files**: 3 files kept
- **Location**: Docker manages log rotation

### Resource Usage
```bash
# View resource usage
docker stats fusetester-api

# View disk usage
docker system df

# Clean up unused images
docker system prune
```

## Database Management

### Backup
```bash
# Create backup
cp /app/fusetester/server/data/fusetester.db /backup/fusetester-$(date +%Y%m%d).db

# Automated backup script
docker compose exec fusetester-api sqlite3 /app/data/fusetester.db ".backup /app/data/backup-$(date +%Y%m%d).db"
```

### Access Database
```bash
# Connect to SQLite database
docker compose exec fusetester-api sqlite3 /app/data/fusetester.db

# Or access from host
sqlite3 /app/fusetester/server/data/fusetester.db
```

## Security Features

### Container Security
- **Non-root user** - Runs as unprivileged user
- **Read-only filesystem** - Except for data directory
- **Minimal base image** - Alpine Linux reduces attack surface
- **No shell access** - Production container doesn't include shell tools

### Network Security
- **Localhost binding** - Only accessible via localhost
- **Nginx proxy** - External access through reverse proxy
- **No direct exposure** - Container not directly accessible from internet

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs fusetester-api

# Check Docker daemon
sudo systemctl status docker

# Rebuild container
docker compose build --no-cache
docker compose up -d
```

### Database Issues
```bash
# Check database file permissions
ls -la /app/fusetester/server/data/

# Test database connection
docker compose exec fusetester-api sqlite3 /app/data/fusetester.db ".tables"

# Reset database (WARNING: deletes all data)
rm /app/fusetester/server/data/fusetester.db
docker compose restart fusetester-api
```

### Performance Issues
```bash
# Check resource usage
docker stats fusetester-api

# Check disk space
df -h /app/fusetester/server/data/

# Clean up logs
docker compose down
docker system prune -f
docker compose up -d
```

### Port Conflicts
```bash
# Check what's using port 3000
sudo lsof -i :3000

# Change port in docker compose.yml if needed
# ports:
#   - "127.0.0.1:3001:3000"
```

## Integration with Nginx

The Docker container works seamlessly with the nginx configuration:
- **Nginx** proxies requests to `127.0.0.1:3000`
- **Container** listens on port 3000 inside the container
- **Docker** maps container:3000 to host:3000
- **Health checks** ensure container availability

## Development vs Production

### Development
```bash
# Run with live logs
docker compose up

# Mount source code for development
# (Add to docker compose.override.yml)
# volumes:
#   - .:/app
```

### Production
```bash
# Run in background
docker compose up -d

# Enable auto-restart
# restart: unless-stopped (already configured)

# Monitor with external tools
# Use Prometheus/Grafana for metrics
```

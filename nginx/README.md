# FuseTester Nginx Configuration

This directory contains nginx configuration files for serving the FuseTester application across two subdomains.

## Configuration Files

### `client.conf`
- **Domain**: `carbot.joeleht.dev`
- **Purpose**: Serves the HTML dashboard (client application)
- **Root Directory**: `/app/fusetester/client`
- **Features**:
  - HTTPS redirect
  - Static file caching
  - Security headers
  - Gzip compression
  - API redirects to API subdomain

### `api.conf`
- **Domain**: `api.carbot.joeleht.dev`
- **Purpose**: Proxies requests to Node.js API server
- **Upstream**: `127.0.0.1:3000` (Node.js server)
- **Features**:
  - HTTPS redirect
  - CORS configuration
  - Rate limiting
  - Request timeouts
  - Health check optimization
  - Load balancing ready

## Installation

1. **Copy configuration files to nginx conf.d directory:**
   ```bash
   sudo ln -s /app/fusetester/nginx/client.conf /etc/nginx/conf.d/carbot.joeleht.dev.conf
   sudo ln -s /app/fusetester/nginx/api.conf /etc/nginx/conf.d/api.carbot.joeleht.dev.conf
   ```

2. **Test nginx configuration:**
   ```bash
   sudo nginx -t
   ```

3. **Reload nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

## SSL Certificates

The configurations assume Let's Encrypt certificates. To obtain them:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificates for both domains
sudo certbot --nginx -d carbot.joeleht.dev
sudo certbot --nginx -d api.carbot.joeleht.dev
```

## Directory Structure

```
/app/fusetester/
├── client/
│   ├── index.html
│   └── README.md
└── server/
    ├── server.js
    ├── package.json
    └── fusetester.db
```

## File Deployment

### Repository Deployment
```bash
# Clone repository directly to deployment directory
git clone https://github.com/jissepo/FuseTester.git /app/fusetester

# Set permissions
sudo chown -R www-data:www-data /app/fusetester
sudo chmod -R 755 /app/fusetester

# Make sure the client directory is readable
sudo chmod -R 755 /app/fusetester/client
```

### Docker Deployment (Server)
```bash
# Navigate to server directory
cd /app/fusetester/server

# Create data directory with proper permissions
mkdir -p data
chmod 777 data

# Build and start the Docker container
docker-compose up -d

# Check container status
docker-compose ps
docker-compose logs fusetester-api
```

### Repository Updates
```bash
# Update the application
cd /app/fusetester
sudo git pull origin main

# Rebuild and restart Docker container
cd /app/fusetester/server
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Docker Service Management

The API server now runs as a Docker container. Here are the management commands:

### Container Management
```bash
# Start the container
cd /app/fusetester/server
docker-compose up -d

# Stop the container
docker-compose down

# View logs
docker-compose logs -f fusetester-api

# Restart container
docker-compose restart fusetester-api

# Check container health
docker-compose ps
```

### Alternative: Systemd Service (Legacy)

If you prefer to run without Docker, you can still create a systemd service:

Create a systemd service for the Node.js API:

```bash
sudo nano /etc/systemd/system/fusetester-api.service
```

```ini
[Unit]
Description=FuseTester API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app/fusetester/server
Environment=NODE_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable fusetester-api
sudo systemctl start fusetester-api
sudo systemctl status fusetester-api
```

### Docker vs Systemd

**Recommended: Docker** (easier deployment, better isolation, easier updates)
- Use `docker-compose up -d` to start
- Database persisted in `./data` directory
- Container auto-restarts on failure
- Easy to update with rebuild

**Alternative: Systemd** (traditional approach)
- Requires Node.js installed on host
- Manual dependency management
- Direct file system access

## Security Features

### Client Security
- HTTPS enforcement
- Security headers (XSS, CSRF protection)
- Content Security Policy
- Static file caching with immutable headers
- Hidden files protection

### API Security
- CORS configuration for carbot.joeleht.dev
- Rate limiting (10 requests/second)
- Request size limits
- Timeout configurations
- Upstream connection pooling

## Monitoring

### Log Files
- Client access: `/var/log/nginx/carbot.joeleht.dev.access.log`
- Client errors: `/var/log/nginx/carbot.joeleht.dev.error.log`
- API access: `/var/log/nginx/api.carbot.joeleht.dev.access.log`
- API errors: `/var/log/nginx/api.carbot.joeleht.dev.error.log`

### Health Checks
- Client: `https://carbot.joeleht.dev/`
- API: `https://api.carbot.joeleht.dev/health`

## Performance Optimizations

- Gzip compression for text assets
- Static file caching with long expiry
- Upstream connection pooling
- HTTP/2 support
- Keep-alive connections

## Troubleshooting

1. **Check nginx status:**
   ```bash
   sudo systemctl status nginx
   ```

2. **Check Docker container:**
   ```bash
   docker-compose ps
   docker-compose logs fusetester-api
   ```

3. **Test configuration:**
   ```bash
   sudo nginx -t
   ```

4. **View logs:**
   ```bash
   sudo tail -f /var/log/nginx/*.log
   ```

5. **Check SSL certificates:**
   ```bash
   sudo certbot certificates
   ```

6. **Fix database permissions (if needed):**
   ```bash
   cd /app/fusetester/server
   mkdir -p data
   chmod 777 data
   docker-compose restart fusetester-api
   ```

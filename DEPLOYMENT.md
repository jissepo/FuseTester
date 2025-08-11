# FuseTester Deployment Guide

This guide covers the complete deployment of the FuseTester application with Docker, nginx, and SSL certificates.

## Prerequisites

- Ubuntu/Debian server with sudo access
- Domain names pointing to your server: `carbot.joeleht.dev` and `api.carbot.joeleht.dev`

## Step 1: Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
# Or run: newgrp docker
```

## Step 2: Clone and Set Up Application

```bash
# Create application directory
sudo mkdir -p /app
cd /app

# Clone repository (replace with your actual repository URL)
sudo git clone https://github.com/zonejoosep/FuseTester.git fusetester

# Set ownership for the application
sudo chown -R $USER:$USER /app/fusetester

# Create and configure data directory for Docker volume
cd /app/fusetester/server
mkdir -p data

# Set permissions for Docker container (user ID 1000)
sudo chown -R 1000:1000 data
chmod 755 data
```

## Step 3: Deploy Docker Container

```bash
cd /app/fusetester/server

# Build and start the container
docker-compose up -d

# Verify container is running
docker-compose ps
docker-compose logs
```

## Step 4: Install and Configure Nginx

```bash
# Install nginx
sudo apt update
sudo apt install nginx -y

# Copy nginx configurations
sudo cp /app/fusetester/nginx/http.conf /etc/nginx/conf.d/
sudo cp /app/fusetester/nginx/api.conf /etc/nginx/conf.d/
sudo cp /app/fusetester/nginx/client.conf /etc/nginx/conf.d/

# Create web root directory
sudo mkdir -p /var/www/carbot.joeleht.dev
sudo cp /app/fusetester/client/index.html /var/www/carbot.joeleht.dev/
sudo chown -R www-data:www-data /var/www/carbot.joeleht.dev

# Test nginx configuration
sudo nginx -t

# If successful, reload nginx
sudo systemctl reload nginx
```

## Step 5: Set Up SSL Certificates

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificates
sudo certbot --nginx -d carbot.joeleht.dev -d api.carbot.joeleht.dev

# Verify auto-renewal
sudo certbot renew --dry-run
```

## Troubleshooting

### Docker Permission Issues

If you see "permission denied" errors with the SQLite database:

```bash
# Check current permissions
ls -la /app/fusetester/server/data

# Fix permissions if needed
sudo chown -R 1000:1000 /app/fusetester/server/data
chmod 755 /app/fusetester/server/data

# Restart container
cd /app/fusetester/server
docker-compose restart
```

### Nginx Configuration Issues

If nginx fails to start:

```bash
# Check nginx error logs
sudo journalctl -u nginx -f

# Test configuration syntax
sudo nginx -t

# Check if http.conf is included in main nginx.conf
grep -n "include.*conf.d" /etc/nginx/nginx.conf
```

### Container Health Check

```bash
# Check if API is responding
curl http://localhost:3000/health

# Check container logs
docker-compose logs -f

# Check container resource usage
docker stats
```

### Port Conflicts

If port 3000 is already in use:

```bash
# Check what's using the port
sudo netstat -tulpn | grep :3000

# Or use lsof
sudo lsof -i :3000
```

## Verification

After deployment, verify everything works:

1. **API Health Check**: `curl https://api.carbot.joeleht.dev/health`
2. **Client Access**: Visit `https://carbot.joeleht.dev`
3. **Container Status**: `docker-compose ps` (should show "Up" status)
4. **Nginx Status**: `sudo systemctl status nginx`

## Maintenance

### Updating the Application

```bash
cd /app/fusetester
git pull origin main

# Rebuild and restart container
cd server
docker-compose build --no-cache
docker-compose up -d
```

### Viewing Logs

```bash
# Application logs
docker-compose logs -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Backup Database

```bash
# The SQLite database is in the Docker volume
cp /app/fusetester/server/data/fusetester.db /backup/location/
```

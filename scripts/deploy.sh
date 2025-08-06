#!/bin/bash

# FuseTester Deployment Script for Raspberry Pi
# Deploys the application to /opt/fusetester and creates systemd service
# Uses Node.js 24.5 via NVM
#
# Prerequisites:
# - NVM and Node.js 24.5 already installed on target system
# - User 'pi' with sudo privileges  
# - pigpio daemon configured
# - Run 'nvm use 24.5.0' before executing this script
#
# Usage: ./scripts/deploy.sh

set -e

echo "Deploying FuseTester to Raspberry Pi..."

# Backup current version if it exists
if [ -d "/opt/fusetester" ]; then
    echo "Creating backup..."
    sudo cp -r /opt/fusetester "/opt/fusetester.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Stop the service if running
if systemctl is-active --quiet fusetester.service; then
    echo "Stopping FuseTester service..."
    sudo systemctl stop fusetester.service
fi

# Copy files to deployment directory
echo "Copying files..."
sudo mkdir -p /opt/fusetester
sudo cp -r . /opt/fusetester/
sudo chown -R pi:pi /opt/fusetester

# Install dependencies
echo "Installing dependencies..."
cd /opt/fusetester

# Verify Node.js is available (should be managed by NVM)
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please ensure NVM and Node.js 24.5 are installed:"
    echo "   Please run: nvm use 24.5.0"
    exit 1
fi

echo "✓ Using Node.js version: $(node --version)"
npm install --production --unsafe-perm

# Update systemd service
echo "Updating systemd service..."
sudo tee /etc/systemd/system/fusetester.service > /dev/null <<EOF
[Unit]
Description=FuseTester Node.js Application
After=network.target pigpiod.service
Requires=pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/fusetester
ExecStart=$(which node) src/main.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# Reload and start service
sudo systemctl daemon-reload
sudo systemctl enable fusetester.service
sudo systemctl start fusetester.service

echo "Deployment completed successfully!"
echo "Service status:"
sudo systemctl status fusetester.service --no-pager

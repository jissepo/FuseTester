#!/bin/bash

# FuseTester Deployment Script for Raspberry Pi
# Deploys the Python application to /opt/fusetester and creates systemd service
#
# Prerequisites:
# - Python 3.9+ already installed on target system
# - User 'garage' with sudo privileges  
# - I2C interface enabled
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
sudo chown -R garage:garage /opt/fusetester

# Setup Python environment
echo "Setting up Python environment..."
cd /opt/fusetester

# Verify Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo "✓ Using Python version: $PYTHON_VERSION"
else
    echo "❌ Python version $PYTHON_VERSION is too old. Requires Python 3.9 or higher"
    exit 1
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Update systemd service
echo "Updating systemd service..."
sudo tee /etc/systemd/system/fusetester.service > /dev/null <<EOF
[Unit]
Description=FuseTester 64-Fuse Monitoring System (Python)
After=network.target
Wants=network.target

[Service]
Type=simple
User=garage
Group=gpio
WorkingDirectory=/opt/fusetester
Environment=PATH=/opt/fusetester/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/fusetester/venv/bin/python3 src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=PYTHONPATH=/opt/fusetester/src
Environment=LOG_LEVEL=INFO
Environment=I2C_ENABLED=true
Environment=DATA_COLLECTION_INTERVAL=5000
Environment=CSV_FILE_PATH=/opt/fusetester/data/fuse_data.csv
Environment=CSV_MAX_FILE_SIZE=52428800
Environment=MEMORY_MONITORING=true

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

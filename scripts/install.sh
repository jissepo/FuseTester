#!/bin/bash

# FuseTester Installation Script for Raspberry Pi 1 B+
# This script installs system dependencies and configures the project
# 
# Prerequisites:
# - Raspberry Pi OS (Pi OS) 
# - Internet connection
# - User 'pi' with sudo privileges
# - NVM installed with Node.js 24.5 (install separately first)
#
# To install NVM and Node.js 24.5 first:
#   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
#   source ~/.bashrc
#   nvm install 24.5.0
#   nvm use 24.5.0
#   nvm alias default 24.5.0
#
# This script will:
# - Update system packages
# - Install pigpio daemon for GPIO/I2C
# - Enable I2C interface
# - Verify Node.js installation
# - Install project dependencies
# - Create systemd service
#
# Usage: ./scripts/install.sh

set -e

echo "Starting FuseTester installation on Raspberry Pi 1 B+"

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get install -y build-essential python3-dev

# Install pigpio daemon and library
echo "Installing pigpio..."
sudo apt-get install -y pigpio python3-pigpio

# Enable and start pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Install I2C tools for debugging
echo "Installing I2C tools..."
sudo apt-get install -y i2c-tools

# Enable I2C interface
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Verify Node.js installation (should be installed via NVM)
echo "Verifying Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install NVM and Node.js 24.5 first:"
    echo "   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo "   source ~/.bashrc"
    echo "   nvm install 24.5.0"
    echo "   nvm use 24.5.0"
    echo "   nvm alias default 24.5.0"
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"

# Create necessary directories
echo "Creating directories..."
mkdir -p logs data

# Install project dependencies
echo "Installing project dependencies..."
npm install --production --unsafe-perm

# Verify I2C setup
echo "Verifying I2C setup..."
if [ -c "/dev/i2c-1" ]; then
    echo "✓ I2C interface available at /dev/i2c-1"
    echo "Scanning for I2C devices..."
    sudo i2cdetect -y 1
else
    echo "⚠ I2C interface not found. Please check configuration."
fi

# Check if pigpio daemon is running
if systemctl is-active --quiet pigpiod; then
    echo "✓ pigpio daemon is running"
else
    echo "⚠ pigpio daemon not running. Starting..."
    sudo systemctl start pigpiod
fi

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/fusetester.service > /dev/null <<EOF
[Unit]
Description=FuseTester I2C Data Collection Application
After=network.target pigpiod.service
Requires=pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
Environment=NVM_DIR=/home/pi/.nvm
ExecStartPre=/bin/bash -c 'source /home/pi/.nvm/nvm.sh && nvm use 24.5.0'
ExecStart=/bin/bash -c 'source /home/pi/.nvm/nvm.sh && nvm use 24.5.0 && node src/main.js'
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable fusetester.service

echo "Installation completed successfully!"
echo "Start data collection with: sudo systemctl start fusetester.service"
echo "Check status with: sudo systemctl status fusetester.service"
echo "View logs with: sudo journalctl -u fusetester.service -f"

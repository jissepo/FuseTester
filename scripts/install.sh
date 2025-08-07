#!/bin/bash

# FuseTester Installation Script for Raspberry Pi 1 B+
# This script installs system dependencies and configures the Python project
# 
# Prerequisites:
# - Raspberry Pi OS (Pi OS) 
# - Internet connection
# - User 'pi' with sudo privileges
# - Python 3.9+ (pre-installed on Pi OS)
#
# This script will:
# - Update system packages
# - Install Python development tools
# - Install hardware access libraries
# - Enable I2C interface
# - Install project dependencies
# - Create Python virtual environment
# - Create systemd service
#
# Usage: ./scripts/install.sh

set -e

echo "Starting FuseTester installation on Raspberry Pi 1 B+"

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages for Python development
echo "Installing system dependencies..."
sudo apt-get install -y build-essential python3-dev python3-pip python3-venv

# Install I2C tools for hardware access
echo "Installing I2C tools..."
sudo apt-get install -y i2c-tools python3-smbus

# Install additional hardware libraries
echo "Installing hardware access libraries..."
sudo apt-get install -y python3-rpi.gpio

# Enable I2C interface
echo "Installing I2C tools..."
sudo apt-get install -y i2c-tools

# Enable I2C interface
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Verify Python installation
echo "Verifying Python installation..."
python3 --version

# Check Python version (require 3.9+)
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo "✓ Python version $PYTHON_VERSION meets requirements (≥3.9)"
else
    echo "❌ Python version $PYTHON_VERSION is too old. Requires Python 3.9 or higher"
    echo "   Please upgrade Python or install from source"
    exit 1
fi

echo "✓ pip3 version: $(pip3 --version)"

# Create necessary directories
echo "Creating directories..."
mkdir -p logs data

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip in virtual environment
echo "Upgrading pip..."
pip install --upgrade pip

# Install project dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Verify I2C setup
echo "Verifying I2C setup..."
if [ -c "/dev/i2c-1" ]; then
    echo "✓ I2C interface available at /dev/i2c-1"
    echo "Scanning for I2C devices..."
    sudo i2cdetect -y 1
else
    echo "⚠ I2C interface not found. Please check configuration."
fi

# Test Python hardware library installation
echo "Testing hardware library installation..."
python3 -c "
try:
    import RPi.GPIO
    import board
    import busio
    import adafruit_ads1x15.ads1115
    print('✓ All hardware libraries imported successfully')
except ImportError as e:
    print(f'❌ Hardware library import failed: {e}')
    exit(1)
"

# Deactivate virtual environment for service creation
deactivate

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/fusetester.service > /dev/null <<EOF
[Unit]
Description=FuseTester 64-Fuse Monitoring System (Python)
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=gpio
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$(pwd)/venv/bin/python3 src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=PYTHONPATH=$(pwd)/src
Environment=LOG_LEVEL=INFO
Environment=I2C_ENABLED=true
Environment=DATA_COLLECTION_INTERVAL=5000
Environment=CSV_FILE_PATH=./data/fuse_data.csv
Environment=CSV_MAX_FILE_SIZE=52428800
Environment=MEMORY_MONITORING=true

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

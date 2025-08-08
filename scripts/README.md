# FuseTester Scripts

This directory contains deployment and management scripts for the FuseTester Python application on Raspberry Pi 1 Model B+.

## Prerequisites

**System Requirements:**

- ✅ Raspberry Pi OS (Pi OS) installed  
- ✅ Python 3.9+ (pre-installed on Pi OS)
- ✅ Internet connection available
- ✅ User 'garage' has sudo privileges
- ✅ SSH access configured (if deploying remotely)

**No additional language runtime installation required** - Python 3.9+ comes pre-installed on Raspberry Pi OS.

## Scripts Overview

### `install.sh`
System installation script that:
- Updates system packages
- Installs Python development tools and hardware libraries
- Installs I2C tools and enables I2C interface
- Creates Python virtual environment
- Installs project dependencies from requirements.txt
- Creates systemd service

**Usage:**
```bash
# Run the installer
chmod +x scripts/install.sh
./scripts/install.sh
```

### `start.sh`  
Application startup script that:
- Activates Python virtual environment
- Checks system resources and Python version
- Sets environment variables
- Starts the fuse monitoring application

**Usage:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

### `deploy.sh`
Production deployment script that:
- Creates backup of existing installation
- Deploys application to `/opt/fusetester`
- Creates Python virtual environment in deployment location
- Updates systemd service configuration

**Usage:**
```bash
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

## Python Environment Management

All scripts use **Python 3.9+** which comes pre-installed on Raspberry Pi OS:
- ✅ Native ARM6 compatibility (Raspberry Pi 1 B+)
- ✅ Virtual environment isolation
- ✅ Hardware library support (RPi.GPIO, CircuitPython)
- ✅ Lower memory footprint (25-40MB vs 80-120MB)

**Virtual Environment:** Scripts automatically create and manage a Python virtual environment for dependency isolation.

## Systemd Service

The scripts create a systemd service (`fusetester.service`) that:
- Automatically starts on boot
- Restarts on failure  
- Uses Python virtual environment
- Runs as the 'garage' user with GPIO group access
- Has access to I2C interface

**Service Commands:**
```bash
# Start service
sudo systemctl start fusetester.service

# Stop service
sudo systemctl stop fusetester.service

# Check status
sudo systemctl status fusetester.service

# View logs
sudo journalctl -u fusetester.service -f

# Enable auto-start on boot
sudo systemctl enable fusetester.service
```

## Hardware Libraries

The Python conversion uses dedicated hardware libraries:
- **RPi.GPIO**: GPIO control for multiplexer management
- **adafruit-circuitpython-ads1x15**: ADS1115 ADC interface
- **adafruit-blinka**: CircuitPython compatibility layer (provides I2C via busio)
- **requests**: HTTP data transmission to external server

## Troubleshooting

**If Python version is too old:**
```bash
# Check Python version
python3 --version
# Should be 3.9 or higher
```

**If I2C is not working:**
```bash
# Check I2C interface
ls /dev/i2c*
# Should show /dev/i2c-1

# Scan for devices
sudo i2cdetect -y 1
```

**If virtual environment fails:**
```bash
# Install venv module
sudo apt-get install python3-venv

# Create manually
python3 -m venv venv
source venv/bin/activate
```

**GPIO Permission Issues:**
```bash
# Add user to gpio group
sudo usermod -a -G gpio garage

# Reboot to apply changes
sudo reboot
```

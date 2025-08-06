# FuseTester Scripts

This directory contains deployment and management scripts for the FuseTester application on Raspberry Pi 1 Model B+.

## Prerequisites

**Before running any scripts, you MUST install NVM and Node.js 24.5:**

```bash
# 1. Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 2. Restart your shell or source the profile
source ~/.bashrc

# 3. Install Node.js 24.5 (ARM6 compatible)
nvm install 24.5.0

# 4. Use Node.js 24.5 as default
nvm use 24.5.0
nvm alias default 24.5.0

# 5. Verify installation
node --version  # Should show v24.5.0
npm --version   # Should show npm version
```

### Additional Prerequisites:
- ✅ Raspberry Pi OS (Pi OS) installed
- ✅ Internet connection available
- ✅ User 'pi' has sudo privileges
- ✅ SSH access configured (if deploying remotely)

## Scripts Overview

### `install.sh`
System installation script that:
- Updates system packages
- Installs pigpio daemon and I2C tools
- **Verifies Node.js 24.5 is installed** (does not install it)
- Installs project dependencies
- Creates systemd service
- Enables I2C interface

**Usage:**
```bash
# Ensure Node.js 24.5 is active first
nvm use 24.5.0

# Then run the installer
chmod +x scripts/install.sh
./scripts/install.sh
```

### `start.sh`
Application startup script that:
- Loads NVM and Node.js 24.5
- Checks system resources
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
- Updates systemd service configuration
- Uses Node.js 24.5 via NVM

**Usage:**
```bash
# Ensure Node.js 24.5 is active first
nvm use 24.5.0

# Then deploy
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

## Node.js Version Management

All scripts expect **Node.js 24.5 LTS** to be installed via **NVM**:
- ✅ ARM6 compatibility (Raspberry Pi 1 B+)
- ✅ Easy version switching
- ✅ User-level installation (no sudo required for npm)
- ✅ Better dependency management

**Important:** Always run `nvm use 24.5.0` before executing scripts!

The systemd service will use the Node.js version that was active when the script was run.

## Systemd Service

The scripts create a systemd service (`fusetester.service`) that:
- Automatically starts on boot
- Restarts on failure
- Uses the correct Node.js version via NVM
- Runs as the 'pi' user
- Depends on pigpio daemon

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

## Prerequisites

Before running these scripts, ensure:
- ✅ Raspberry Pi OS (Pi OS) installed
- ✅ Internet connection available
- ✅ User 'pi' has sudo privileges
- ✅ SSH access configured (if deploying remotely)

## Troubleshooting

**If Node.js is not found:**
```bash
# Manually load NVM
source ~/.nvm/nvm.sh
nvm use 24.5.0
```

**If I2C is not working:**
```bash
# Check I2C interface
ls /dev/i2c*
# Should show /dev/i2c-1

# Scan for devices
sudo i2cdetect -y 1
```

**If pigpio daemon is not running:**
```bash
# Start pigpio daemon
sudo systemctl start pigpiod
sudo systemctl enable pigpiod
```

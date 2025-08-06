# Raspberry Pi Setup Guide

This guide walks you through setting up your Raspberry Pi 1 Model B+ for running the FuseTester I2C data collection application.

## Initial Pi Setup

### 1. Install Pi OS
- Download Pi OS Lite from the official Raspberry Pi website
- Flash it to your MicroSD card using Raspberry Pi Imager
- Enable SSH by creating an empty `ssh` file in the boot partition

### 2. First Boot Configuration
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y curl wget git htop

# Configure timezone
sudo dpkg-reconfigure tzdata

# Enable SSH (if not already enabled)
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 3. Memory Optimization
Since the Pi 1 B+ only has 512MB RAM, optimize memory usage:

```bash
# Reduce GPU memory split
echo "gpu_mem=16" | sudo tee -a /boot/config.txt

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-country

# Configure swap
sudo dphys-swapfile swapoff
sudo sed -i 's/#CONF_SWAPSIZE=100/CONF_SWAPSIZE=512/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 4. Network Configuration

#### WiFi Setup (if using WiFi)
```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add your network:
```
network={
    ssid="YourNetworkName"
    psk="YourPassword"
}
```

#### Static IP (optional)
```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

## I2C and Hardware Setup

### Enable I2C Interface
```bash
# Method 1: Using raspi-config
sudo raspi-config
# Navigate to: Interface Options > I2C > Enable

# Method 2: Edit config directly
echo 'dtparam=i2c_arm=on' | sudo tee -a /boot/config.txt
sudo reboot
```

### Install pigpio
```bash
# Install system packages
sudo apt-get install -y pigpio python3-pigpio i2c-tools

# Enable and start pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Verify I2C Setup
```bash
# Check I2C interface exists
ls /dev/i2c*

# Scan for I2C devices
sudo i2cdetect -y 1

# Check pigpio daemon status
sudo systemctl status pigpiod
```

## Application Installation

### 1. Clone and Install
```bash
cd /opt
sudo git clone <your-repo-url> fusetester
cd fusetester
sudo chown -R pi:pi /opt/fusetester
```

### 2. Run Installation Script
```bash
chmod +x scripts/install.sh
sudo ./scripts/install.sh
```

### 3. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit as needed
```

## Service Management

### Start/Stop Service
```bash
sudo systemctl start fusetester.service
sudo systemctl stop fusetester.service
sudo systemctl restart fusetester.service
```

### Check Status and Logs
```bash
sudo systemctl status fusetester.service
sudo journalctl -u fusetester.service -f
```

### Enable Auto-Start
```bash
sudo systemctl enable fusetester.service
```

## Data Collection

### CSV Files
- Data files are stored in `/opt/fusetester/data/`
- Files are automatically rotated when size limit is reached
- Format: `timestamp,device,register,value`

### Monitoring Data Collection
```bash
# Watch CSV file in real-time
tail -f /opt/fusetester/data/sensor_data.csv

# Check application logs
tail -f /opt/fusetester/logs/combined.log

# Monitor memory usage
free -h
```

## I2C Device Connection

### Hardware Wiring
Connect I2C devices to the Pi:
- **Device VCC** → **Pi 3.3V** (pin 1 or 17)
- **Device GND** → **Pi Ground** (pin 6, 9, 14, 20, 25, 30, 34, or 39)
- **Device SDA** → **Pi SDA** (GPIO 2, pin 3)
- **Device SCL** → **Pi SCL** (GPIO 3, pin 5)

### Connecting Devices via Code
Edit your `.env` file or modify the application to connect to specific I2C devices at startup.

## Performance Monitoring

### System Resources
```bash
# Memory usage
free -h

# CPU usage
htop

# Disk usage
df -h

# Temperature
vcgencmd measure_temp

# I2C bus status
sudo i2cdetect -y 1
```

## Troubleshooting

### Common Issues

#### Out of Memory
- Check swap configuration
- Monitor memory usage: `free -h`
- Review application logs for memory warnings

#### I2C Communication Errors
```bash
# Check pigpio daemon
sudo systemctl status pigpiod

# Verify I2C interface
ls /dev/i2c*

# Scan for devices
sudo i2cdetect -y 1

# Check permissions
sudo usermod -a -G gpio,i2c pi
```

#### Service Won't Start
```bash
# Check service logs
sudo journalctl -u fusetester.service --no-pager -l

# Check file permissions
ls -la /opt/fusetester

# Verify Node.js installation
which node
node --version
```

#### CSV File Issues
```bash
# Check data directory permissions
ls -la /opt/fusetester/data/

# Monitor disk space
df -h

# Check file rotation
ls -la /opt/fusetester/data/*.csv
```

## Security Considerations

### Basic Security
```bash
# Change default password
passwd

# Update packages regularly
sudo apt-get update && sudo apt-get upgrade -y

# Configure firewall (if needed for remote access)
sudo ufw enable
sudo ufw allow ssh
```

### File Permissions
```bash
# Ensure proper ownership
sudo chown -R pi:pi /opt/fusetester

# Make scripts executable
chmod +x /opt/fusetester/scripts/*.sh
```

## Backup and Recovery

### Application Backup
```bash
# Backup application and data
tar -czf fusetester-backup-$(date +%Y%m%d).tar.gz /opt/fusetester

# Backup just data files
tar -czf data-backup-$(date +%Y%m%d).tar.gz /opt/fusetester/data/
```

### Recovery
```bash
# Restore from backup
cd /opt
sudo rm -rf fusetester
sudo tar -xzf fusetester-backup-*.tar.gz
sudo systemctl restart fusetester.service
```

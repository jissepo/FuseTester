# FuseTester

64-fuse monitoring system for Raspberry Pi 1 Model B+ using Python, I2C ADC, and GPIO multiplexers.

## Hardware Requirements

- Raspberry Pi 1 Model B+ (ARM6 armv6l architecture)
- 512MB RAM 
- MicroSD card (8GB+ recommended)
- Pi OS (Raspberry Pi OS) with Python 3.9+
- Hardware components:
  - ADS1115 16-bit I2C ADC
  - 4x CD74HC4067M 16-channel analog multiplexers
  - GPIO connections for multiplexer control

## Quick Start

**No additional software installation required** - Python 3.9+ comes pre-installed on Pi OS.

1. Clone this repository to your Raspberry Pi:
```bash
git clone <repository-url>
cd FuseTester
```

2. Run the installation script:
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env file as needed
```

4. Start the service:
```bash
sudo systemctl start fusetester.service
```

5. Check service status:
```bash
sudo systemctl status fusetester.service
```

6. View logs:
```bash
sudo journalctl -u fusetester.service -f
```

## Service Management

The application runs as a systemd service after installation:

```bash
# Start the service
sudo systemctl start fusetester.service

# Stop the service
sudo systemctl stop fusetester.service

# Restart the service
sudo systemctl restart fusetester.service

# Check service status
sudo systemctl status fusetester.service

# View live logs
sudo journalctl -u fusetester.service -f

# Enable auto-start on boot (already done by install script)
sudo systemctl enable fusetester.service
```

## Configuration

All configuration is handled through the `.env` file:

- `I2C_ENABLED` - Enable/disable I2C functionality
- `DATA_COLLECTION_INTERVAL` - Data collection frequency (seconds)  
- `SERVER_URL` - HTTP endpoint for data transmission
- `API_KEY` - Authentication key for HTTP requests
- `DEVICE_ID` - Unique identifier for this device
- `HTTP_TIMEOUT` - HTTP request timeout (seconds)
- `MAX_BUFFER_SIZE` - Number of readings to buffer when offline
- `LOG_LEVEL` - Logging level (INFO, DEBUG, ERROR)
- `MEMORY_MONITORING` - Enable memory usage logging

## Fuse Monitoring System

This application monitors 64 fuses using:
- **4 CD74HC4067M multiplexers** (16 channels each)
- **1 ADS1115 16-bit ADC** (I2C address 0x48)
- **GPIO pins** for multiplexer control (S0=27, S1=17, S2=24, S3=23)
- **HTTP data transmission** with offline fallback buffer

Data is collected every 5 seconds (configurable) and logged with the format:
```
timestamp,fuse 1,fuse 2,fuse 3,...,fuse 64
```

## Data Collection

The application continuously monitors all 64 fuses and transmits voltage readings via HTTP POST requests to an external server. The monitoring cycle:

1. Select multiplexer (0-3)
2. Select channel on multiplexer (0-15) 
3. Read voltage from ADS1115 ADC
4. Transmit data via HTTP POST to external server
5. Clean variables for memory optimization
6. Repeat for all 64 channels

## File Management

- Data transmission includes automatic retry with exponential backoff
- When HTTP server is unreachable, data is buffered in memory for later transmission
- Buffer has configurable size limit to prevent memory exhaustion on Pi 1 B+
- Log files stored in `logs/` directory
- No local data files - all fuse readings transmitted via HTTP

## Development

### Local Development (Not on Pi)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Note: Hardware-specific features won't work without Pi hardware
python3 src/main.py
```

**Note:** Direct Python execution is only for development/testing. On the Pi, use the systemd service instead.

### Hardware Libraries Used

- **RPi.GPIO**: GPIO control for multiplexer management
- **adafruit-circuitpython-ads1x15**: ADS1115 ADC interface  
- **adafruit-blinka**: CircuitPython compatibility layer
- **smbus2**: Alternative I2C communication
- **psutil**: System resource monitoring

### Monitoring

The application includes built-in monitoring for:
- Memory usage (critical for Pi 1 B+ with 512MB RAM)
- System health and resource usage
- HTTP transmission status and buffer usage
- I2C device connectivity and status
- GPIO pin states and multiplexer control

## Scripts

- `scripts/install.sh` - Complete installation on Pi
- `scripts/start.sh` - Application startup script  
- `scripts/deploy.sh` - Production deployment script

See `scripts/README.md` for detailed script documentation.

## License

ISC

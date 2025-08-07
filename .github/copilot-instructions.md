# Copilot Instructions - FuseTester

## Project Overview

This is a Python I2C data collection and CSV logging application designed to run on a Raspberry Pi 1 Model B+ with Pi OS (Raspberry Pi OS). The project is optimized for the ARM6 architecture and limited resources of the Pi 1 B+. It collects data from I2C devices and stores it in CSV files without running a web server.

## Hardware Specifications

- **Target Device**: Raspberry Pi 1 Model B+
- **Architecture**: ARM6 (armv6l)
- **RAM**: 512MB
- **CPU**: Single-core 700MHz ARM1176JZF-S
- **Operating System**: Pi OS (Raspberry Pi OS)

## Technology Stack

- **Runtime**: Python 3.9+ (pre-installed on Pi OS)
- **Package Manager**: pip3
- **Architecture**: ARM6 compatible packages only
- **Data Storage**: CSV files (no database)
- **Configuration**: .env files only (no JSON config files)

## Project Structure

```
FuseTester/
├── .github/
│   └── copilot-instructions.md
├── src/
│   ├── main.py                     # Main application entry point
│   └── services/
│       ├── i2c_service.py          # I2C communication service
│       ├── gpio_service.py         # GPIO multiplexer control
│       ├── ads1115_service.py      # ADS1115 ADC interface
│       ├── csv_logger.py           # CSV data logging
│       └── fuse_monitor_service.py # Main monitoring coordinator
├── data/                           # CSV data files directory
├── docs/
│   ├── README.md
│   └── SETUP.md                    # Pi setup instructions
├── scripts/
│   ├── install.sh                  # Pi installation script
│   ├── start.sh                    # Startup script
│   └── deploy.sh                   # Deployment script
├── logs/                           # Application logs
├── requirements.txt                # Python dependencies
├── .gitignore
├── .env.example                    # Environment variables template
└── README.md
```

## Development Guidelines

### Python Compatibility

- Use Python 3.9+ (pre-installed on Pi OS)
- Leverage dedicated hardware libraries for Pi components
- Use virtual environments for dependency isolation
- Test all packages for ARM6 compatibility before adding dependencies
- **Primary Libraries**:
  - **RPi.GPIO** - Native GPIO control for multiplexer management
  - **adafruit-circuitpython-ads1x15** - Dedicated ADS1115 ADC library
  - **smbus2** or **board/busio** - I2C communication
  - **pigpio** - Alternative GPIO/I2C library for precise timing

### Hardware Library Selection

- **GPIO Control**: Use RPi.GPIO for simplicity, pigpio for precision timing
- **I2C Communication**: Use adafruit-circuitpython libraries for sensors
- **ADC Interface**: Use adafruit-circuitpython-ads1x15 for ADS1115
- **CSV Handling**: Built-in csv module or pandas for advanced operations
- **Configuration**: python-dotenv for .env file support

### Performance Considerations

- **Memory Management**: Pi 1 B+ has only 512MB RAM
  - Use lightweight packages and avoid memory-heavy dependencies
  - Implement proper garbage collection practices
  - Monitor memory usage with `psutil` or system tools
  - Python has lower memory overhead than Node.js runtimes
- **CPU Optimization**: Single-core 700MHz processor
  - Use asyncio for non-blocking I/O operations
  - Implement proper exception handling and timeouts
  - Leverage Python's efficient built-in data structures
- **I2C Communication**: Handle I2C timeouts and errors gracefully
  - Use dedicated hardware libraries for robust communication
  - Implement retry logic for transient failures

### Code Style and Patterns

- Follow PEP 8 style guidelines
- Use type hints for better code documentation
- Implement modular architecture with clear separation of concerns
- Use environment variables for configuration (.env files only)
- Implement proper logging with the logging module
- **Hardware Service Pattern**: Use singleton classes for hardware management
- **CSV Logging**: Use csv module or pandas for efficient data logging
- **No Web Server**: Focus on data collection and CSV storage

### Package Management

- Use requirements.txt for dependency management
- Pin exact versions for reproducible builds
- Prefer packages with native ARM6 support
- **Required Hardware Libraries**:
  - `RPi.GPIO>=0.7.1` - GPIO control
  - `adafruit-circuitpython-ads1x15>=2.2.0` - ADS1115 ADC
  - `adafruit-blinka>=8.0.0` - CircuitPython compatibility layer
  - `smbus2>=0.4.0` - I2C communication (alternative)
- **Optional Libraries**:
  - `pigpio>=1.78` - Advanced GPIO/I2C control
  - `pandas>=1.5.0` - Advanced CSV operations (memory permitting)
- Use virtual environments (venv) for development
- Test installations on actual Pi hardware

### File Handling

- Use absolute paths for file operations
- Implement proper file locking for concurrent access
- Handle file system permissions appropriately for Pi OS
- Use context managers (with statements) for file operations
- **CSV File Management**: Use csv module or pandas with chunking for large files
- Implement automatic file rotation based on size

### Error Handling

- Use comprehensive try-except blocks with specific exceptions
- Implement proper logging with the logging module
- Handle system-level errors (low memory, disk space) with psutil
- Implement graceful shutdown procedures with signal handlers

### Configuration Management

- Use python-dotenv for environment variable management
- Support environment-specific config files
- Implement configuration validation with type checking
- Document all configuration options with default values

### Security Considerations

- Implement proper input validation
- Use secure defaults for all configurations
- Handle file permissions correctly for Pi OS
- Use HTTPS for external communications

### Testing

- Use pytest for unit testing framework
- Write unit tests for all core functionality
- Include integration tests for Pi-specific hardware features
- Test on actual Pi hardware before deployment
- Use mock libraries for testing without hardware
- Implement automated testing where possible

## Pi-Specific Considerations

### GPIO and Hardware Access

- **Primary GPIO Library**: Use RPi.GPIO for standard GPIO operations
- **Alternative**: Use pigpio for precise timing and advanced features
- **I2C Communication**: Use adafruit-circuitpython libraries for sensors
- **ADS1115 ADC**: Use adafruit-circuitpython-ads1x15 for reliable readings
- Handle hardware interrupts properly with callback functions
- **I2C Setup**: Enable I2C interface via raspi-config
- **I2C Pins**: SDA (GPIO 2, pin 3), SCL (GPIO 3, pin 5)
- **GPIO Pins for Multiplexer Control**:
  - S0=27, S1=17, S2=24, S3=23 (Channel select)
  - Enable pins for 4 multiplexers
- Document pin configurations and hardware requirements
- Implement device-specific error handling with proper exception types

### System Integration

- Use systemd for service management with proper Python service files
- Implement proper logging to system journals via logging module
- Handle system updates and reboots gracefully
- Monitor system resources with psutil library
- Use signal handlers for graceful shutdown

### Network Configuration

- Handle WiFi/Ethernet configuration changes
- Implement network reconnection logic
- Support both static and DHCP configurations
- Handle network timeouts and failures

### Storage Management

- Monitor disk space usage
- Implement log rotation
- Handle SD card write limitations
- Use appropriate file systems and mount options

## Deployment Guidelines

- Create deployment scripts for Pi OS
- Document required system packages and dependencies
- Implement automated backup procedures
- Provide rollback procedures
- Document performance tuning options

## Common Commands

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Install system packages for hardware access
sudo apt-get install python3-dev python3-pip

# Enable I2C interface
sudo raspi-config nonint do_i2c 0

# Start application
python3 src/main.py

# Run with systemd service
sudo systemctl start fusetester.service

# Monitor system resources
htop
free -h
df -h

# Check GPIO permissions
groups $USER  # Should include gpio group
```

## Troubleshooting

- Check ARM6 compatibility for failing packages
- Monitor memory usage during development with psutil
- Use Python debugger (pdb) for debugging issues
- Check Pi OS system logs for hardware issues
- Verify GPIO permissions and group membership
- Test I2C devices with i2cdetect command
- Verify hardware connections and pull-up resistors
- Check for hardware library conflicts (RPi.GPIO vs pigpio)

## Resources

- [Python on Raspberry Pi](https://www.raspberrypi.org/documentation/usage/python/)
- [Pi OS documentation](https://www.raspberrypi.org/documentation/)
- [Adafruit CircuitPython Libraries](https://circuitpython.readthedocs.io/)
- [RPi.GPIO Documentation](https://sourceforge.net/projects/raspberry-gpio-python/)
- [ADS1115 Python Library](https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15)

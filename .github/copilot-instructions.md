# Copilot Instructions - FuseTester

## Project Overview

This is a Node.js I2C data collection and CSV logging application designed to run on a Raspberry Pi 1 Model B+ with Pi OS (Raspberry Pi OS). The project is optimized for the ARM6 architecture and limited resources of the Pi 1 B+. It collects data from I2C devices and stores it in CSV files without running a web server.

## Hardware Specifications

- **Target Device**: Raspberry Pi 1 Model B+
- **Architecture**: ARM6 (armv6l)
- **RAM**: 512MB
- **CPU**: Single-core 700MHz ARM1176JZF-S
- **Operating System**: Pi OS (Raspberry Pi OS)

## Technology Stack

- **Runtime**: Node.js (LTS version 24.5)
- **Package Manager**: npm
- **Architecture**: ARM6 compatible packages only
- **Data Storage**: CSV files (no database)
- **Configuration**: .env files only (no JSON config files)

## Project Structure

```
FuseTester/
├── .github/
│   └── copilot-instructions.md
├── src/
│   ├── main.js                    # Main application entry point
├── data/                            # CSV data files directory
├── docs/
│   ├── README.md
│   └── SETUP.md                    # Pi setup instructions
├── scripts/
│   ├── install.sh                  # Pi installation script
│   ├── start.sh                    # Startup script
│   └── deploy.sh                   # Deployment script
├── logs/                            # Application logs
├── package.json
├── package-lock.json
├── .gitignore
├── .env.example                    # Environment variables template
└── README.md
```

## Development Guidelines

### Node.js Compatibility

- Use Node.js LTS version 24.5
- Avoid packages that require native compilation unless ARM6 compatible
- Use `--unsafe-perm` flag for global npm installations if needed
- Test all packages for ARM6 compatibility before adding dependencies
- **Primary I2C Library**: Use `pigpio` for reliable I2C communication

### Performance Considerations

- **Memory Management**: Pi 1 B+ has only 512MB RAM
  - Use lightweight packages and avoid memory-heavy dependencies
  - Implement proper garbage collection practices
  - Monitor memory usage with `process.memoryUsage()`
- **CPU Optimization**: Single-core 700MHz processor
  - Avoid CPU-intensive synchronous operations
  - Use asynchronous programming patterns
  - Implement proper error handling and timeouts
- **I2C Communication**: Handle I2C timeouts and errors gracefully

### Code Style and Patterns

- Use ES6+ features supported by the Node.js version
- Implement modular architecture with clear separation of concerns
- Use environment variables for configuration (.env files only)
- Implement proper logging with log levels
- **I2C Service Pattern**: Use singleton service for I2C device management
- **CSV Logging**: Use streaming for efficient data logging
- **No Web Server**: Focus on data collection and CSV storage

### Package Management

- Pin exact versions in package.json for reproducible builds
- Prefer packages with native ARM6 support
- **Required for I2C**: `pigpio` package with system pigpio daemon
- Avoid packages requiring Python 2.7 or build tools if possible
- Test installations on actual Pi hardware
- Use `biome` for linting and formatting

### File Handling

- Use absolute paths for file operations
- Implement proper file locking for concurrent access
- Handle file system permissions appropriately for Pi OS
- Use streaming for large file operations to conserve memory
- **CSV File Management**: Implement automatic file rotation based on size

### Error Handling

- Implement comprehensive error handling and logging
- Use process monitoring for automatic restarts
- Handle system-level errors (low memory, disk space)
- Implement graceful shutdown procedures

### Configuration Management

- Use environment-specific config files
- Support environment variable configuration
- Implement configuration validation
- Document all configuration options

### Security Considerations

- Implement proper input validation
- Use secure defaults for all configurations
- Handle file permissions correctly for Pi OS
- Use HTTPS for external communications

### Testing

- Write unit tests for all core functionality
- Include integration tests for Pi-specific features
- Test on actual Pi hardware before deployment
- Implement automated testing where possible

## Pi-Specific Considerations

### GPIO and Hardware Access

- Use `pigpio` for GPIO control and I2C communication
- Handle hardware interrupts properly
- Implement device-specific error handling
- Document pin configurations and hardware requirements
- **I2C Setup**: Enable I2C interface and start pigpio daemon
- **I2C Pins**: SDA (GPIO 2, pin 3), SCL (GPIO 3, pin 5)
- Implement device-specific error handling
- Document pin configurations and hardware requirements

### System Integration

- Use systemd for service management
- Implement proper logging to system journals
- Handle system updates and reboots gracefully
- Monitor system resources and health

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
# Install Node.js on Pi 1 B+
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install project dependencies
npm install --production

# Start application
npm start

# Monitor system resources
htop
free -h
df -h
```

## Troubleshooting

- Check ARM6 compatibility for failing packages
- Monitor memory usage during development
- Use `strace` for debugging system calls
- Check Pi OS system logs for hardware issues
- Verify GPIO permissions and configurations

## Resources

- [Node.js ARM6 builds](https://nodejs.org/dist/)
- [Pi OS documentation](https://www.raspberrypi.org/documentation/)
- [ARM6 compatible npm packages](https://www.npmjs.com/search?q=arm6)

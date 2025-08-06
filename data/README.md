# Data Directory

This directory contains CSV files with sensor data collected from I2C devices.

## File Structure
- `sensor_data.csv` - Current active data file
- `sensor_data_YYYY-MM-DDTHH-MM-SS.csv` - Rotated data files

## CSV Format
```
timestamp,device,register,value
2025-08-07T12:00:00.000Z,0x48,0x00,25
2025-08-07T12:00:05.000Z,0x48,0x00,26
```

## File Rotation
Files are automatically rotated when they exceed the configured size limit (default: 10MB).

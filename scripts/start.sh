#!/bin/bash

# FuseTester Startup Script
# Starts the fuse monitoring application using Python 3.9+
#
# Prerequisites:
# - Python 3.9+ installed
# - Virtual environment created and dependencies installed
# - I2C interface enabled and configured
#
# Usage: ./scripts/start.sh

set -e

echo "Starting FuseTester..."

# Activate Python virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated Python virtual environment"
else
    echo "Warning: Virtual environment not found, using system Python"
fi

# Verify Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python version: $PYTHON_VERSION"

# Check if running on Pi
ARCH=$(uname -m)
echo "Architecture: $ARCH"

if [[ "$ARCH" == "armv6l" ]]; then
    echo "✓ Running on Raspberry Pi 1 B+ (ARM6)"
elif [[ "$ARCH" == "armv7l" || "$ARCH" == "aarch64" ]]; then
    echo "Running on newer Pi architecture: $ARCH"
else
    echo "Warning: Not running on ARM architecture"
fi

# Check available memory
AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
echo "Available memory: ${AVAILABLE_MEM}MB"

if [ "$AVAILABLE_MEM" -lt 100 ]; then
    echo "Warning: Low available memory (${AVAILABLE_MEM}MB)"
fi

# Set Python path
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Set default environment variables
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export I2C_ENABLED=${I2C_ENABLED:-true}
export DATA_COLLECTION_INTERVAL=${DATA_COLLECTION_INTERVAL:-5.0}
export CSV_FILE_PATH=${CSV_FILE_PATH:-./data/fuse_data.csv}
export MEMORY_MONITORING=${MEMORY_MONITORING:-true}

echo "Environment configured:"
echo "  LOG_LEVEL=$LOG_LEVEL"
echo "  I2C_ENABLED=$I2C_ENABLED"
echo "  DATA_COLLECTION_INTERVAL=${DATA_COLLECTION_INTERVAL}s"
echo "  CSV_FILE_PATH=$CSV_FILE_PATH"

# Start the application
exec python3 src/main.py

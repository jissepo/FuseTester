#!/bin/bash

# FuseTester Startup Script
# Starts the fuse monitoring application using Node.js 24.5 via NVM
#
# Prerequisites:
# - NVM installed with Node.js 24.5
# - Project dependencies installed
# - I2C and pigpio properly configured
#
# Usage: ./scripts/start.sh

set -e

echo "Starting FuseTester..."

# Load NVM and use Node.js 24.5
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Ensure we're using Node.js 24.5
nvm use 24.5.0

# Verify Node.js version
echo "Using Node.js version: $(node --version)"

# Check if running on Pi
if [[ $(uname -m) != "armv6l" ]]; then
    echo "Warning: Not running on ARM6 architecture"
fi

# Check available memory
AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
echo "Available memory: ${AVAILABLE_MEM}MB"

if [ "$AVAILABLE_MEM" -lt 100 ]; then
    echo "Warning: Low available memory (${AVAILABLE_MEM}MB)"
fi

# Set environment
export NODE_ENV=${NODE_ENV:-production}

# Start the application
exec node src/main.js

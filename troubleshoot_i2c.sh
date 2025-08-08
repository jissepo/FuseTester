#!/bin/bash
"""
I2C Troubleshooting Script for FuseTester
Diagnose I2C connection issues with ADS1115 ADC

Run this script to check I2C configuration and connections
"""

echo "🔍 FuseTester I2C Diagnostic Script"
echo "===================================="
echo ""

# Check if I2C is enabled
echo "1. Checking I2C interface status..."
if [ -e /dev/i2c-1 ]; then
    echo "✓ I2C interface enabled (/dev/i2c-1 exists)"
else
    echo "❌ I2C interface not found!"
    echo "   Run: sudo raspi-config"
    echo "   Navigate to: Interfacing Options -> I2C -> Enable"
    echo "   Then reboot the Pi"
    exit 1
fi

# Check I2C permissions
echo ""
echo "2. Checking I2C permissions..."
if groups $USER | grep -q "i2c"; then
    echo "✓ User '$USER' is in i2c group"
else
    echo "⚠️  User '$USER' not in i2c group"
    echo "   Run: sudo usermod -a -G i2c $USER"
    echo "   Then log out and back in"
fi

# Check I2C tools installation
echo ""
echo "3. Checking I2C tools..."
if command -v i2cdetect &> /dev/null; then
    echo "✓ i2c-tools installed"
else
    echo "❌ i2c-tools not installed"
    echo "   Run: sudo apt-get install i2c-tools"
    exit 1
fi

# Scan I2C bus
echo ""
echo "4. Scanning I2C bus..."
echo "   Expected ADS1115 address: 0x48 (default)"
echo ""
sudo i2cdetect -y 1

# Check for ADS1115 specifically
echo ""
echo "5. Checking for ADS1115..."
if sudo i2cdetect -y 1 | grep -q "48"; then
    echo "✓ ADS1115 detected at address 0x48"
else
    echo "❌ ADS1115 not detected at 0x48"
    echo ""
    echo "Possible causes:"
    echo "• Loose I2C connections (SDA/SCL)"
    echo "• Power supply issue (VDD not connected or insufficient)"
    echo "• Ground connection problem"
    echo "• ADS1115 address jumpers changed"
    echo "• Faulty ADS1115 module"
    echo ""
    echo "Hardware checklist:"
    echo "📌 VDD → 3.3V or 5V"
    echo "📌 GND → Ground"
    echo "📌 SCL → GPIO 3 (Pin 5)"
    echo "📌 SDA → GPIO 2 (Pin 3)"
    echo "📌 ADDR → GND (for 0x48 address)"
fi

# Check voltage on I2C pins
echo ""
echo "6. I2C pin status..."
echo "   GPIO 2 (SDA): Pin 3"
echo "   GPIO 3 (SCL): Pin 5"
echo ""
echo "   Check with multimeter:"
echo "   • Both pins should read ~3.3V when idle (pull-up resistors)"
echo "   • Pins should toggle when I2C communication occurs"

# Check kernel messages for I2C errors
echo ""
echo "7. Recent kernel messages (I2C related)..."
echo "   Looking for I2C errors in system logs..."
if dmesg | grep -i i2c | tail -5 | grep -q .; then
    echo "Recent I2C messages:"
    dmesg | grep -i i2c | tail -5
else
    echo "   No recent I2C messages in kernel log"
fi

echo ""
echo "8. Troubleshooting steps to try:"
echo ""
echo "🔧 Power cycle:"
echo "   sudo shutdown -h now"
echo "   (Disconnect power, wait 10 seconds, reconnect)"
echo ""
echo "🔧 Re-enable I2C:"
echo "   sudo raspi-config"
echo "   Interfacing Options -> I2C -> Disable -> Enable"
echo "   sudo reboot"
echo ""
echo "🔧 Check connections:"
echo "   • Verify all 4 wires: VDD, GND, SDA, SCL"
echo "   • Ensure solid connections (no loose wires)"
echo "   • Try different jumper wires"
echo ""
echo "🔧 Test with different address:"
echo "   • Connect ADDR pin to VDD (should show 0x49)"
echo "   • Connect ADDR pin to SDA (should show 0x4A)"
echo "   • Connect ADDR pin to SCL (should show 0x4B)"
echo ""
echo "🔧 Check power supply:"
echo "   • Measure voltage between VDD and GND (should be 3.3V or 5V)"
echo "   • Ensure Pi power supply is adequate (2.5A+ recommended)"

echo ""
echo "Run this script again after trying fixes to see if ADS1115 is detected."

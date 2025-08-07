#!/usr/bin/env python3
"""
FuseTester System Test
Basic functionality test for Python services
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_imports():
    """Test if all modules can be imported"""
    print("Testing Python imports...")
    
    try:
        from services.i2c_service import I2CService
        from services.gpio_service import GPIOService  
        from services.ads1115_service import ADS1115Service
        from services.csv_logger import CSVLogger
        from services.fuse_monitor_service import FuseMonitorService
        print("✓ All service modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_hardware_libraries():
    """Test hardware library availability"""
    print("\nTesting hardware libraries...")
    
    libraries = {
        'RPi.GPIO': 'GPIO control',
        'board': 'CircuitPython board interface',
        'busio': 'CircuitPython I2C bus',
        'adafruit_ads1x15.ads1115': 'ADS1115 ADC library',
        'psutil': 'System monitoring'
    }
    
    all_passed = True
    
    for lib, description in libraries.items():
        try:
            __import__(lib)
            print(f"✓ {lib} - {description}")
        except ImportError:
            print(f"❌ {lib} - {description} (not available)")
            all_passed = False
    
    return all_passed

async def test_service_creation():
    """Test basic service instantiation"""
    print("\nTesting service creation...")
    
    try:
        # Note: These won't actually initialize hardware in test mode
        from services.csv_logger import CSVLogger
        csv_logger = CSVLogger()
        print("✓ CSVLogger created")
        
        return True
    except Exception as e:
        print(f"❌ Service creation failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("FuseTester Python Conversion Test")
    print("=" * 40)
    
    # Configure basic logging
    logging.basicConfig(level=logging.WARNING)
    
    tests = [
        test_imports(),
        test_hardware_libraries(), 
        test_service_creation()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    passed = sum(1 for result in results if result is True)
    total = len(results)
    
    print(f"\nTest Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed - Python conversion successful!")
        sys.exit(0)
    else:
        print("❌ Some tests failed - check hardware library installation")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

"""
I2C Service for FuseTester
Handles I2C communication using adafruit-circuitpython libraries
Optimized for Raspberry Pi 1 Model B+ ARM6 architecture
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice

logger = logging.getLogger(__name__)

class I2CService:
    """I2C communication service using CircuitPython libraries"""
    
    def __init__(self):
        self.initialized = False
        self.i2c_bus: Optional[busio.I2C] = None
        self.connected_devices: Dict[int, I2CDevice] = {}
    
    async def initialize(self):
        """Initialize I2C service"""
        if self.initialized:
            logger.info("I2C service already initialized")
            return
        
        try:
            logger.info("Initializing I2C service...")
            
            # Initialize I2C bus using CircuitPython
            self.i2c_bus = busio.I2C(board.SCL, board.SDA, frequency=100000)
            
            # Test I2C bus availability
            if not self.i2c_bus.try_lock():
                raise RuntimeError("Could not acquire I2C bus lock")
            
            # Release the lock for normal operation
            self.i2c_bus.unlock()
            
            self.initialized = True
            logger.info("I2C service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize I2C service: {e}")
            raise
    
    async def connect_device(self, address: int) -> I2CDevice:
        """
        Connect to an I2C device
        
        Args:
            address: I2C device address (7-bit)
            
        Returns:
            I2CDevice instance
        """
        if not self.initialized:
            raise RuntimeError("I2C service not initialized")
        
        if address in self.connected_devices:
            return self.connected_devices[address]
        
        try:
            # Create I2C device instance
            device = I2CDevice(self.i2c_bus, address)
            self.connected_devices[address] = device
            
            logger.info(f"Connected to I2C device at address 0x{address:02x}")
            return device
            
        except Exception as e:
            logger.error(f"Failed to connect to I2C device 0x{address:02x}: {e}")
            raise
    
    async def write_word_data(self, address: int, register: int, data: int):
        """
        Write 16-bit word data to a register
        
        Args:
            address: I2C device address
            register: Register address
            data: 16-bit data to write
        """
        device = await self.connect_device(address)
        
        try:
            # Convert to big-endian format for I2C
            high_byte = (data >> 8) & 0xFF
            low_byte = data & 0xFF
            buffer = bytes([register, high_byte, low_byte])
            
            # Write with device context manager
            with device:
                device.write(buffer)
                
            # Small delay for device processing
            await asyncio.sleep(0.001)
            
        except Exception as e:
            logger.error(f"Failed to write word data to 0x{address:02x} reg 0x{register:02x}: {e}")
            raise
    
    async def read_word_data(self, address: int, register: int) -> int:
        """
        Read 16-bit word data from a register
        
        Args:
            address: I2C device address
            register: Register address
            
        Returns:
            16-bit data value
        """
        device = await self.connect_device(address)
        
        try:
            # Write register address first, then read data
            write_buffer = bytes([register])
            read_buffer = bytearray(2)
            
            with device:
                device.write_then_readinto(write_buffer, read_buffer)
            
            # Convert from big-endian
            value = (read_buffer[0] << 8) | read_buffer[1]
            return value
            
        except Exception as e:
            logger.error(f"Failed to read word data from 0x{address:02x} reg 0x{register:02x}: {e}")
            raise
    
    async def scan_bus(self) -> list[int]:
        """
        Scan I2C bus for connected devices
        
        Returns:
            List of detected device addresses
        """
        if not self.initialized:
            raise RuntimeError("I2C service not initialized")
        
        devices = []
        logger.info("Scanning I2C bus...")
        
        try:
            # Lock the bus for scanning
            while not self.i2c_bus.try_lock():
                await asyncio.sleep(0.01)
            
            try:
                # Scan common I2C addresses (0x08 to 0x77)
                for address in range(0x08, 0x78):
                    try:
                        # Try to communicate with the device
                        self.i2c_bus.writeto(address, bytes())
                        devices.append(address)
                        logger.info(f"Found device at address 0x{address:02x}")
                    except OSError:
                        # No device at this address
                        pass
                    except Exception as e:
                        logger.debug(f"Error scanning address 0x{address:02x}: {e}")
            finally:
                self.i2c_bus.unlock()
                
        except Exception as e:
            logger.error(f"Failed to scan I2C bus: {e}")
            raise
        
        logger.info(f"I2C scan complete. Found {len(devices)} devices: "
                   f"{[f'0x{addr:02x}' for addr in devices]}")
        return devices
    
    async def test_device(self, address: int) -> bool:
        """
        Test if a device is responsive at the given address
        
        Args:
            address: I2C device address to test
            
        Returns:
            True if device responds, False otherwise
        """
        try:
            device = await self.connect_device(address)
            
            # Try a simple communication test
            with device:
                # Just try to acquire the device - if it fails, device is not present
                pass
            
            logger.debug(f"Device 0x{address:02x} is responsive")
            return True
            
        except Exception as e:
            logger.debug(f"Device 0x{address:02x} test failed: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current I2C service status
        
        Returns:
            Status dictionary
        """
        return {
            'initialized': self.initialized,
            'connected_devices': list(self.connected_devices.keys()),
            'bus_frequency': 100000 if self.i2c_bus else None
        }
    
    async def shutdown(self):
        """Shutdown I2C service and cleanup resources"""
        if not self.initialized:
            return
        
        try:
            logger.info("Shutting down I2C service...")
            
            # Clear connected devices
            self.connected_devices.clear()
            
            # Deinitialize I2C bus if available
            if self.i2c_bus:
                try:
                    self.i2c_bus.deinit()
                except Exception as e:
                    logger.warning(f"Error deinitializing I2C bus: {e}")
            
            self.initialized = False
            logger.info("I2C service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during I2C service shutdown: {e}")
    
    def is_initialized(self) -> bool:
        """Check if I2C service is initialized"""
        return self.initialized

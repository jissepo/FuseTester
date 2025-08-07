"""
GPIO Service for Multiplexer Control
Handles GPIO operations for CD74HC4067M multiplexers using RPi.GPIO
Optimized for Raspberry Pi 1 Model B+ ARM6 architecture
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

# GPIO Pin definitions for CD74HC4067M multiplexers
MUX_CONTROL_PINS = {
    'S0': 27,  # Pi Pin 13 (GPIO27)
    'S1': 17,  # Pi Pin 11 (GPIO17) 
    'S2': 24,  # Pi Pin 18 (GPIO24)
    'S3': 23,  # Pi Pin 16 (GPIO23)
}

MUX_ENABLE_PINS = {
    'MUX0': 7,   # Pi Pin 26 (GPIO7)
    'MUX1': 8,   # Pi Pin 24 (GPIO8)
    'MUX2': 6,   # Pi Pin 31 (GPIO6)
    'MUX3': 13,  # Pi Pin 33 (GPIO13)
}

class GPIOService:
    """GPIO service for controlling CD74HC4067M multiplexers"""
    
    def __init__(self):
        self.initialized = False
        self.current_mux: Optional[int] = None
        self.current_channel: Optional[int] = None
    
    async def initialize(self):
        """Initialize GPIO pins for multiplexer control"""
        if self.initialized:
            logger.info("GPIO service already initialized")
            return
        
        try:
            logger.info("Initializing GPIO service...")
            
            # Set GPIO mode to BCM (Broadcom pin numbering)
            GPIO.setmode(GPIO.BCM)
            
            # Disable GPIO warnings (common on Pi systems)
            GPIO.setwarnings(False)
            
            # Initialize control pins (S0, S1, S2, S3) as outputs
            for pin_name, pin_number in MUX_CONTROL_PINS.items():
                GPIO.setup(pin_number, GPIO.OUT, initial=GPIO.LOW)
                logger.debug(f"Initialized control pin {pin_name} (GPIO{pin_number}) as output")
            
            # Initialize enable pins as outputs (active low, so start high = disabled)
            for mux_name, pin_number in MUX_ENABLE_PINS.items():
                GPIO.setup(pin_number, GPIO.OUT, initial=GPIO.HIGH)
                logger.debug(f"Initialized enable pin {mux_name} (GPIO{pin_number}) as output (disabled)")
            
            # Ensure all multiplexers start disabled
            await self.disable_all_mux()
            
            self.initialized = True
            logger.info("GPIO service initialized successfully")
            logger.info(f"Control pins: {MUX_CONTROL_PINS}")
            logger.info(f"Enable pins: {MUX_ENABLE_PINS}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO service: {e}")
            await self.cleanup()
            raise
    
    async def set_mux_channel(self, channel: int):
        """
        Set multiplexer channel (0-15)
        
        Args:
            channel: Channel number (0-15)
        """
        if not self.initialized:
            raise RuntimeError("GPIO service not initialized")
        
        if not 0 <= channel <= 15:
            raise ValueError("Channel must be 0-15")
        
        try:
            # Convert channel to binary and set S0, S1, S2, S3 pins
            GPIO.output(MUX_CONTROL_PINS['S0'], channel & 0x01)
            GPIO.output(MUX_CONTROL_PINS['S1'], (channel & 0x02) >> 1)
            GPIO.output(MUX_CONTROL_PINS['S2'], (channel & 0x04) >> 2)
            GPIO.output(MUX_CONTROL_PINS['S3'], (channel & 0x08) >> 3)
            
            self.current_channel = channel
            logger.debug(f"Set multiplexer channel to {channel}")
            
            # Small settling delay for multiplexer switching
            await asyncio.sleep(0.001)
            
        except Exception as e:
            logger.error(f"Failed to set multiplexer channel {channel}: {e}")
            raise
    
    async def enable_mux(self, mux_index: int):
        """
        Enable a specific multiplexer (disable others)
        
        Args:
            mux_index: Multiplexer index (0-3)
        """
        if not self.initialized:
            raise RuntimeError("GPIO service not initialized")
        
        if not 0 <= mux_index <= 3:
            raise ValueError("Multiplexer index must be 0-3")
        
        try:
            # First disable all multiplexers
            await self.disable_all_mux()
            
            # Enable the specified multiplexer (active low)
            mux_names = ['MUX0', 'MUX1', 'MUX2', 'MUX3']
            mux_name = mux_names[mux_index]
            GPIO.output(MUX_ENABLE_PINS[mux_name], GPIO.LOW)
            
            self.current_mux = mux_index
            logger.debug(f"Enabled multiplexer {mux_index} ({mux_name})")
            
            # Small settling delay for multiplexer enabling
            await asyncio.sleep(0.002)
            
        except Exception as e:
            logger.error(f"Failed to enable multiplexer {mux_index}: {e}")
            raise
    
    async def disable_all_mux(self):
        """Disable all multiplexers"""
        if not self.initialized:
            return
        
        try:
            # Set all enable pins high (disabled)
            for pin_number in MUX_ENABLE_PINS.values():
                GPIO.output(pin_number, GPIO.HIGH)
            
            self.current_mux = None
            logger.debug("All multiplexers disabled")
            
        except Exception as e:
            logger.error(f"Failed to disable all multiplexers: {e}")
            raise
    
    async def select_fuse(self, fuse_number: int):
        """
        Select a specific fuse (1-64) by setting appropriate mux and channel
        
        Args:
            fuse_number: Fuse number (1-64)
        """
        if not 1 <= fuse_number <= 64:
            raise ValueError("Fuse number must be 1-64")
        
        # Convert fuse number to mux and channel (0-based internally)
        fuse_index = fuse_number - 1  # Convert to 0-based
        mux_index = fuse_index // 16   # 16 channels per mux
        channel = fuse_index % 16      # Channel within mux
        
        logger.debug(f"Selecting fuse {fuse_number}: mux={mux_index}, channel={channel}")
        
        try:
            # Set the channel first
            await self.set_mux_channel(channel)
            
            # Enable the appropriate multiplexer
            await self.enable_mux(mux_index)
            
            logger.debug(f"Selected fuse {fuse_number} successfully")
            
        except Exception as e:
            logger.error(f"Failed to select fuse {fuse_number}: {e}")
            raise
    
    async def test_gpio_pins(self) -> Dict[str, bool]:
        """
        Test GPIO pin functionality
        
        Returns:
            Dictionary with test results for each pin
        """
        if not self.initialized:
            raise RuntimeError("GPIO service not initialized")
        
        results = {}
        
        try:
            # Test control pins
            for pin_name, pin_number in MUX_CONTROL_PINS.items():
                try:
                    # Test by setting high then low
                    GPIO.output(pin_number, GPIO.HIGH)
                    await asyncio.sleep(0.001)
                    GPIO.output(pin_number, GPIO.LOW)
                    results[f"control_{pin_name}"] = True
                except Exception as e:
                    logger.error(f"Control pin {pin_name} test failed: {e}")
                    results[f"control_{pin_name}"] = False
            
            # Test enable pins
            for mux_name, pin_number in MUX_ENABLE_PINS.items():
                try:
                    # Test by setting low then high (active low)
                    GPIO.output(pin_number, GPIO.LOW)
                    await asyncio.sleep(0.001)
                    GPIO.output(pin_number, GPIO.HIGH)
                    results[f"enable_{mux_name}"] = True
                except Exception as e:
                    logger.error(f"Enable pin {mux_name} test failed: {e}")
                    results[f"enable_{mux_name}"] = False
            
            # Reset all pins to default state
            await self.disable_all_mux()
            for pin_number in MUX_CONTROL_PINS.values():
                GPIO.output(pin_number, GPIO.LOW)
                
        except Exception as e:
            logger.error(f"GPIO pin test failed: {e}")
        
        return results
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current GPIO service status
        
        Returns:
            Status dictionary
        """
        return {
            'initialized': self.initialized,
            'current_mux': self.current_mux,
            'current_channel': self.current_channel,
            'control_pins': MUX_CONTROL_PINS,
            'enable_pins': MUX_ENABLE_PINS
        }
    
    async def cleanup(self):
        """Cleanup GPIO resources"""
        try:
            if self.initialized:
                logger.info("Cleaning up GPIO resources...")
                
                # Disable all multiplexers
                await self.disable_all_mux()
                
                # Reset control pins to low
                for pin_number in MUX_CONTROL_PINS.values():
                    try:
                        GPIO.output(pin_number, GPIO.LOW)
                    except Exception as e:
                        logger.warning(f"Error resetting GPIO{pin_number}: {e}")
            
            # Clean up all GPIO
            GPIO.cleanup()
            
            self.initialized = False
            self.current_mux = None
            self.current_channel = None
            
            logger.info("GPIO cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
    
    async def shutdown(self):
        """Shutdown GPIO service"""
        await self.cleanup()
    
    def is_initialized(self) -> bool:
        """Check if GPIO service is initialized"""
        return self.initialized

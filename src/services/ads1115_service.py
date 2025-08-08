"""
ADS1115 ADC Service
Handles communication with the ADS1115 16-bit ADC using Adafruit CircuitPython library
Optimized for Raspberry Pi 1 Model B+ ARM6 architecture
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

logger = logging.getLogger(__name__)

# ADS1115 I2C address (default)
ADS1115_ADDRESS = 0x48

# Gain settings for different voltage ranges (using raw gain values)
GAIN_SETTINGS = {
    '6.144V': 2/3,  # +/-6.144V range (TWOTHIRDS)
    '4.096V': 1,    # +/-4.096V range (ONE)
    '2.048V': 2,    # +/-2.048V range (TWO)
    '1.024V': 4,    # +/-1.024V range (FOUR)
    '0.512V': 8,    # +/-0.512V range (EIGHT)
    '0.256V': 16    # +/-0.256V range (SIXTEEN)
}

class ADS1115Service:
    """ADS1115 16-bit ADC service using Adafruit CircuitPython library"""
    
    def __init__(self, address: int = ADS1115_ADDRESS):
        self.address = address
        self.initialized = False
        self.ads: Optional[ADS.ADS1115] = None
        self.i2c: Optional[busio.I2C] = None
        self.current_gain = 1  # Default to +/-4.096V range (ONE)
        self.channels: Dict[int, AnalogIn] = {}
    
    async def initialize(self):
        """Initialize connection to ADS1115"""
        if self.initialized:
            logger.info("ADS1115 service already initialized")
            return
        
        try:
            logger.info(f"Initializing ADS1115 at address 0x{self.address:02x}...")
            
            # Create I2C bus
            self.i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
            
            # Create ADS1115 instance
            self.ads = ADS.ADS1115(self.i2c, address=self.address, gain=self.current_gain)
            
            # Test connection by reading configuration
            await self.test_connection()
            
            self.initialized = True
            logger.info("ADS1115 ADC initialized successfully")
            logger.info(f"Current gain setting: {self._gain_to_voltage_range(self.current_gain)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ADS1115: {e}")
            await self.cleanup()
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to ADS1115"""
        if not self.ads:
            return False
        
        try:
            # Try to read from channel 0 to test connection
            test_channel = AnalogIn(self.ads, ADS.P0)
            test_value = test_channel.value
            logger.debug(f"ADS1115 connection test successful, test value: {test_value}")
            return True
            
        except Exception as e:
            logger.error(f"ADS1115 connection test failed: {e}")
            return False
    
    def set_gain(self, gain_setting: str):
        """
        Set the gain/voltage range for readings
        
        Args:
            gain_setting: Gain setting ('6.144V', '4.096V', '2.048V', '1.024V', '0.512V', '0.256V')
        """
        if not self.initialized:
            raise RuntimeError("ADS1115 service not initialized")
        
        if gain_setting not in GAIN_SETTINGS:
            raise ValueError(f"Invalid gain setting. Must be one of: {list(GAIN_SETTINGS.keys())}")
        
        try:
            self.current_gain = GAIN_SETTINGS[gain_setting]
            self.ads.gain = self.current_gain
            
            # Clear cached channels since gain changed
            self.channels.clear()
            
            logger.info(f"ADS1115 gain set to {gain_setting}")
            
        except Exception as e:
            logger.error(f"Failed to set ADS1115 gain: {e}")
            raise
    
    def _gain_to_voltage_range(self, gain) -> str:
        """Convert gain value to voltage range string"""
        for voltage_range, gain_value in GAIN_SETTINGS.items():
            if gain_value == gain:
                return voltage_range
        return "unknown"
    
    def _get_channel(self, channel_num: int) -> AnalogIn:
        """Get or create AnalogIn channel instance"""
        if channel_num not in self.channels:
            channel_pins = [ADS.P0, ADS.P1, ADS.P2, ADS.P3]
            if not 0 <= channel_num <= 3:
                raise ValueError("Channel must be 0-3")
            
            self.channels[channel_num] = AnalogIn(self.ads, channel_pins[channel_num])
        
        return self.channels[channel_num]
    
    async def read_channel(self, channel: int) -> float:
        """
        Read voltage from a specific channel (0-3)
        
        Args:
            channel: ADC channel (0-3)
            
        Returns:
            Voltage reading in volts
        """
        if not self.initialized:
            raise RuntimeError("ADS1115 not initialized")
        
        if not 0 <= channel <= 3:
            raise ValueError("Channel must be 0-3")
        
        try:
            # Get the channel instance
            analog_channel = self._get_channel(channel)
            
            # Read voltage (the library handles the conversion from raw ADC value)
            voltage = analog_channel.voltage
            
            logger.debug(f"Read channel {channel}: {voltage:.4f}V")
            return voltage
            
        except Exception as e:
            logger.error(f"Failed to read ADS1115 channel {channel}: {e}")
            raise
    
    async def read_raw_channel(self, channel: int) -> int:
        """
        Read raw ADC value from a specific channel (0-3)
        
        Args:
            channel: ADC channel (0-3)
            
        Returns:
            Raw 16-bit ADC reading
        """
        if not self.initialized:
            raise RuntimeError("ADS1115 not initialized")
        
        if not 0 <= channel <= 3:
            raise ValueError("Channel must be 0-3")
        
        try:
            # Get the channel instance  
            analog_channel = self._get_channel(channel)
            
            # Read raw value
            raw_value = analog_channel.value
            
            logger.debug(f"Read raw channel {channel}: {raw_value}")
            return raw_value
            
        except Exception as e:
            logger.error(f"Failed to read raw ADS1115 channel {channel}: {e}")
            raise
    
    async def read_all_channels(self) -> Dict[int, float]:
        """
        Read voltage from all 4 channels
        
        Returns:
            Dictionary mapping channel numbers to voltage readings
        """
        if not self.initialized:
            raise RuntimeError("ADS1115 not initialized")
        
        results = {}
        
        try:
            for channel in range(4):
                voltage = await self.read_channel(channel)
                results[channel] = voltage
                
                # Small delay between readings to prevent I2C bus congestion
                await asyncio.sleep(0.01)
            
            logger.debug(f"Read all channels: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to read all ADS1115 channels: {e}")
            raise
    
    async def test_all_channels(self) -> Dict[str, Any]:
        """
        Test all ADC channels
        
        Returns:
            Test results dictionary
        """
        if not self.initialized:
            raise RuntimeError("ADS1115 not initialized")
        
        results = {
            'connection': False,
            'channels': {},
            'error': None
        }
        
        try:
            # Test connection first
            results['connection'] = await self.test_connection()
            
            if results['connection']:
                # Test all channels
                for channel in range(4):
                    try:
                        voltage = await self.read_channel(channel)
                        raw_value = await self.read_raw_channel(channel)
                        
                        results['channels'][channel] = {
                            'voltage': voltage,
                            'raw': raw_value,
                            'success': True
                        }
                        
                    except Exception as e:
                        results['channels'][channel] = {
                            'error': str(e),
                            'success': False
                        }
                        logger.error(f"Channel {channel} test failed: {e}")
                    
                    # Small delay between channel tests
                    await asyncio.sleep(0.05)
                    
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"ADS1115 test failed: {e}")
        
        return results
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current ADS1115 service status
        
        Returns:
            Status dictionary
        """
        return {
            'initialized': self.initialized,
            'address': f"0x{self.address:02x}",
            'gain': self._gain_to_voltage_range(self.current_gain),
            'active_channels': list(self.channels.keys())
        }
    
    async def cleanup(self):
        """Cleanup ADS1115 resources"""
        try:
            if self.initialized:
                logger.info("Cleaning up ADS1115 resources...")
                
                # Clear channel instances
                self.channels.clear()
                
                # Deinitialize I2C bus
                if self.i2c:
                    try:
                        self.i2c.deinit()
                    except Exception as e:
                        logger.warning(f"Error deinitializing I2C bus: {e}")
            
            self.initialized = False
            self.ads = None
            self.i2c = None
            
            logger.info("ADS1115 cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during ADS1115 cleanup: {e}")
    
    async def shutdown(self):
        """Shutdown ADS1115 service"""
        await self.cleanup()
    
    def is_initialized(self) -> bool:
        """Check if ADS1115 service is initialized"""
        return self.initialized

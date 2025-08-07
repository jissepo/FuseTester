"""
Fuse Monitor Service
Coordinates GPIO, ADS1115 ADC, and CSV logging for 64-fuse monitoring system
Optimized for Raspberry Pi 1 Model B+ ARM6 architecture
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .gpio_service import GPIOService
from .ads1115_service import ADS1115Service
from .csv_logger import CSVLogger

logger = logging.getLogger(__name__)

class FuseMonitorService:
    """Main service coordinating fuse monitoring system"""
    
    def __init__(self):
        self.initialized = False
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Hardware configuration
        self.total_fuses = 64  # 4 muxes × 16 channels each
        self.total_muxes = 4
        self.channels_per_mux = 16
        
        # Service instances
        self.gpio_service: Optional[GPIOService] = None
        self.ads1115_service: Optional[ADS1115Service] = None
        self.csv_logger: Optional[CSVLogger] = None
        
        # Monitoring configuration
        self.data_collection_interval = 5.0  # seconds
        self.current_mux = 0
        self.current_channel = 0
    
    async def initialize(self):
        """Initialize all services"""
        if self.initialized:
            logger.info("Fuse Monitor Service already initialized")
            return
        
        try:
            logger.info("Initializing Fuse Monitor Service...")
            
            # Initialize GPIO service
            self.gpio_service = GPIOService()
            await self.gpio_service.initialize()
            logger.info("GPIO service ready")
            
            # Initialize ADS1115 ADC
            self.ads1115_service = ADS1115Service()
            await self.ads1115_service.initialize()
            
            # Set appropriate gain for fuse monitoring (typically 0-5V)
            self.ads1115_service.set_gain('6.144V')  # +/-6.144V range for 0-5V fuse signals
            logger.info("ADS1115 ADC ready")
            
            # Initialize CSV logger
            csv_file_path = os.getenv('CSV_FILE_PATH', './data/fuse_data.csv')
            self.csv_logger = CSVLogger()
            await self.csv_logger.initialize(csv_file_path)
            
            # Write CSV headers for all 64 fuses
            await self._ensure_csv_headers()
            logger.info("CSV logger ready")
            
            # Get monitoring configuration
            self.data_collection_interval = float(os.getenv('DATA_COLLECTION_INTERVAL', 5.0))
            
            self.initialized = True
            logger.info("Fuse Monitor Service initialized successfully")
            logger.info(f"Monitoring configuration: {self.total_fuses} fuses, "
                       f"{self.data_collection_interval}s interval")
            
        except Exception as e:
            logger.error(f"Failed to initialize Fuse Monitor Service: {e}")
            await self.cleanup()
            raise
    
    async def _ensure_csv_headers(self):
        """Ensure CSV file has proper headers for all 64 fuses"""
        try:
            headers = ['timestamp']
            
            # Add headers for all 64 fuses
            for fuse_num in range(1, self.total_fuses + 1):
                headers.append(f'fuse {fuse_num}')
            
            await self.csv_logger.write_headers(headers)
            logger.info(f"CSV headers configured for {self.total_fuses} fuses")
            
        except Exception as e:
            logger.error(f"Failed to configure CSV headers: {e}")
            raise
    
    async def test_system(self) -> Dict[str, Any]:
        """
        Run comprehensive system test
        
        Returns:
            Dictionary with test results
        """
        if not self.initialized:
            raise RuntimeError("Fuse Monitor Service not initialized")
        
        test_results = {
            'gpio': False,
            'adc': False,
            'csv': False,
            'fuse_test': {},
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            logger.info("Running system test...")
            
            # Test GPIO functionality
            gpio_test = await self.gpio_service.test_gpio_pins()
            test_results['gpio'] = all(gpio_test.values())
            test_results['gpio_details'] = gpio_test
            
            # Test ADS1115 ADC
            adc_test = await self.ads1115_service.test_all_channels()
            test_results['adc'] = adc_test.get('connection', False)
            test_results['adc_details'] = adc_test
            
            # Test CSV logger
            csv_status = await self.csv_logger.get_status()
            test_results['csv'] = csv_status.get('initialized', False)
            test_results['csv_details'] = csv_status
            
            # Test a few sample fuses
            if test_results['gpio'] and test_results['adc']:
                test_fuses = [1, 17, 33, 49]  # One from each mux
                for fuse_num in test_fuses:
                    try:
                        voltage = await self._read_fuse(fuse_num)
                        test_results['fuse_test'][fuse_num] = {
                            'voltage': voltage,
                            'success': True
                        }
                    except Exception as e:
                        test_results['fuse_test'][fuse_num] = {
                            'error': str(e),
                            'success': False
                        }
                        logger.error(f"Fuse {fuse_num} test failed: {e}")
            
            # Overall test result
            test_results['overall'] = (test_results['gpio'] and 
                                     test_results['adc'] and 
                                     test_results['csv'])
            
            logger.info(f"System test complete. Overall result: {test_results['overall']}")
            return test_results
            
        except Exception as e:
            test_results['error'] = str(e)
            logger.error(f"System test failed: {e}")
            return test_results
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        if not self.initialized:
            raise RuntimeError("Fuse Monitor Service not initialized")
        
        if self.monitoring:
            logger.info("Monitoring already started")
            return
        
        try:
            logger.info(f"Starting fuse monitoring every {self.data_collection_interval}s")
            
            self.monitoring = True
            self.monitor_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("Fuse monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            self.monitoring = False
            raise
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        if not self.monitoring:
            return
        
        try:
            logger.info("Stopping fuse monitoring...")
            
            self.monitoring = False
            
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
                self.monitor_task = None
            
            # Disable all multiplexers
            if self.gpio_service:
                await self.gpio_service.disable_all_mux()
            
            logger.info("Fuse monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring loop...")
        
        try:
            while self.monitoring:
                start_time = asyncio.get_event_loop().time()
                
                # Collect data from all fuses
                fuse_data = await self._collect_all_fuse_data()
                
                # Log to CSV
                await self.csv_logger.log_fuse_readings(fuse_data)
                
                # Calculate actual collection time
                collection_time = asyncio.get_event_loop().time() - start_time
                logger.debug(f"Data collection completed in {collection_time:.2f}s")
                
                # Sleep for remaining interval time
                sleep_time = max(0, self.data_collection_interval - collection_time)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"Data collection took longer than interval "
                                 f"({collection_time:.2f}s > {self.data_collection_interval}s)")
                    
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            self.monitoring = False
            raise
    
    async def _collect_all_fuse_data(self) -> Dict[int, float]:
        """
        Collect voltage readings from all 64 fuses
        
        Returns:
            Dictionary mapping fuse numbers to voltage readings
        """
        fuse_data = {}
        
        try:
            # Iterate through all muxes and channels
            for mux_index in range(self.total_muxes):
                for channel in range(self.channels_per_mux):
                    fuse_number = (mux_index * self.channels_per_mux) + channel + 1
                    
                    try:
                        voltage = await self._read_fuse(fuse_number)
                        fuse_data[fuse_number] = voltage
                        
                    except Exception as e:
                        logger.error(f"Failed to read fuse {fuse_number}: {e}")
                        fuse_data[fuse_number] = 0.0  # Use 0V for failed readings
            
            logger.debug(f"Collected data from {len(fuse_data)} fuses")
            return fuse_data
            
        except Exception as e:
            logger.error(f"Failed to collect fuse data: {e}")
            raise
    
    async def _read_fuse(self, fuse_number: int) -> float:
        """
        Read voltage from a specific fuse
        
        Args:
            fuse_number: Fuse number (1-64)
            
        Returns:
            Voltage reading in volts
        """
        if not 1 <= fuse_number <= self.total_fuses:
            raise ValueError(f"Fuse number must be 1-{self.total_fuses}")
        
        try:
            # Select the appropriate multiplexer and channel
            await self.gpio_service.select_fuse(fuse_number)
            
            # Small settling delay for multiplexer switching
            await asyncio.sleep(0.005)
            
            # Read from ADC channel 0 (all mux outputs go to AIN0)
            voltage = await self.ads1115_service.read_channel(0)
            
            # Update tracking variables
            fuse_index = fuse_number - 1
            self.current_mux = fuse_index // self.channels_per_mux
            self.current_channel = fuse_index % self.channels_per_mux
            
            return voltage
            
        except Exception as e:
            logger.error(f"Failed to read fuse {fuse_number}: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current system status
        
        Returns:
            Status dictionary
        """
        status = {
            'initialized': self.initialized,
            'monitoring': self.monitoring,
            'current_mux': self.current_mux,
            'current_channel': self.current_channel,
            'data_collection_interval': self.data_collection_interval,
            'total_fuses': self.total_fuses
        }
        
        # Add service statuses
        if self.gpio_service:
            status['gpio'] = await self.gpio_service.get_status()
        
        if self.ads1115_service:
            status['adc'] = await self.ads1115_service.get_status()
        
        if self.csv_logger:
            status['csv'] = await self.csv_logger.get_status()
        
        return status
    
    async def cleanup(self):
        """Cleanup all services"""
        try:
            logger.info("Cleaning up Fuse Monitor Service...")
            
            # Stop monitoring
            await self.stop_monitoring()
            
            # Cleanup services
            if self.csv_logger:
                await self.csv_logger.cleanup()
            
            if self.ads1115_service:
                await self.ads1115_service.cleanup()
            
            if self.gpio_service:
                await self.gpio_service.cleanup()
            
            self.initialized = False
            logger.info("Fuse Monitor Service cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during Fuse Monitor Service cleanup: {e}")
    
    async def shutdown(self):
        """Shutdown Fuse Monitor Service"""
        await self.cleanup()
    
    def is_initialized(self) -> bool:
        """Check if Fuse Monitor Service is initialized"""
        return self.initialized

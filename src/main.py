#!/usr/bin/env python3
"""
FuseTester - 64-Fuse Monitoring System
Main application entry point for Raspberry Pi 1 Model B+

This module initializes and coordinates all services for monitoring 64 fuses
using ADS1115 ADCs and CD74HC4067M multiplexers via I2C and GPIO.
"""

import os
import sys
import signal
import time
import logging
import asyncio
import psutil
from pathlib import Path
from dotenv import load_dotenv

# Import our services
from services.i2c_service import I2CService
from services.fuse_monitor_service import FuseMonitorService

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging():
    """Configure logging with file and console output"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create handlers
    file_handler = logging.FileHandler('logs/fusetester.log')
    error_handler = logging.FileHandler('logs/error.log')
    error_handler.setLevel(logging.ERROR)  # Only log errors and above
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Configure logging format
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            error_handler,
            console_handler
        ]
    )
    
    return logging.getLogger('fusetester')

# Initialize logger
logger = setup_logging()

# Global references for services
i2c_service = None
fuse_monitor_service = None

def log_memory_usage():
    """Log current memory usage - critical for Pi 1 B+ with 512MB RAM"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    logger.info(f"Memory Usage: "
               f"RSS={memory_info.rss / 1024 / 1024:.1f}MB, "
               f"VMS={memory_info.vms / 1024 / 1024:.1f}MB")
    
    # Log system memory if available
    try:
        system_memory = psutil.virtual_memory()
        logger.info(f"System Memory: "
                   f"Used={system_memory.used / 1024 / 1024:.1f}MB, "
                   f"Available={system_memory.available / 1024 / 1024:.1f}MB, "
                   f"Percent={system_memory.percent}%")
    except Exception as e:
        logger.warning(f"Could not get system memory info: {e}")

def create_data_directory():
    """Create data directory if it doesn't exist"""
    csv_file_path = os.getenv('CSV_FILE_PATH', './data/fuse_data.csv')
    data_dir = Path(csv_file_path).parent
    
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created data directory: {data_dir}")

async def initialize_services():
    """Initialize all required services"""
    global i2c_service, fuse_monitor_service
    
    logger.info("Initializing FuseTester Fuse Monitoring System...")
    logger.info(f"Platform: {sys.platform}, Python: {sys.version}")
    
    # Create data directory
    create_data_directory()
    
    # Initialize I2C service if enabled
    if os.getenv('I2C_ENABLED', 'true').lower() == 'true':
        try:
            i2c_service = I2CService()
            await i2c_service.initialize()
            logger.info("I2C service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize I2C service: {e}")
            sys.exit(1)
    else:
        logger.error("I2C is disabled - cannot run fuse monitoring without I2C")
        sys.exit(1)
    
    # Initialize Fuse Monitor Service
    try:
        fuse_monitor_service = FuseMonitorService()
        await fuse_monitor_service.initialize()
        logger.info("Fuse Monitor Service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Fuse Monitor Service: {e}")
        sys.exit(1)
    
    logger.info("FuseTester initialization complete")

async def start_monitoring():
    """Start the fuse monitoring system"""
    logger.info("Starting fuse monitoring system...")
    
    try:
        # Run system test first
        logger.info("Running system test...")
        test_results = await fuse_monitor_service.test_system()
        logger.info(f"System test results: {test_results}")
        
        # Start monitoring if test passed
        if test_results.get('adc') and not test_results.get('error'):
            await fuse_monitor_service.start_monitoring()
            logger.info("Fuse monitoring started successfully")
            
            # Log system status
            status = await fuse_monitor_service.get_status()
            logger.info(f"System status: {status}")
        else:
            logger.error("System test failed - cannot start monitoring")
            logger.error(f"Test results: {test_results}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        sys.exit(1)
    
    # Start periodic memory monitoring if enabled
    if os.getenv('MEMORY_MONITORING', 'true').lower() == 'true':
        asyncio.create_task(periodic_memory_monitoring())
    
    # Start periodic status logging
    asyncio.create_task(periodic_status_logging())

async def periodic_memory_monitoring():
    """Periodic memory usage logging"""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        try:
            log_memory_usage()
        except Exception as e:
            logger.warning(f"Error during memory monitoring: {e}")

async def periodic_status_logging():
    """Periodic system status logging"""
    while True:
        await asyncio.sleep(600)  # 10 minutes
        try:
            if fuse_monitor_service:
                status = await fuse_monitor_service.get_status()
                logger.info(f"System status update: "
                           f"monitoring={status.get('monitoring')}, "
                           f"current_mux={status.get('current_mux')}, "
                           f"current_channel={status.get('current_channel')}, "
                           f"csv_size={status.get('csv', {}).get('size_mb', 'unknown')}MB")
        except Exception as e:
            logger.warning(f"Error during status logging: {e}")

def shutdown_handler(signum, frame):
    """Graceful shutdown handler"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    asyncio.create_task(shutdown())

async def shutdown():
    """Shutdown all services gracefully"""
    logger.info("Shutting down gracefully...")
    
    try:
        # Stop monitoring
        if fuse_monitor_service:
            await fuse_monitor_service.shutdown()
        
        # Shutdown I2C
        if i2c_service:
            await i2c_service.shutdown()
        
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)

def handle_exception(loop, context):
    """Global exception handler for asyncio"""
    logger.error(f"Unhandled exception: {context}")
    asyncio.create_task(shutdown())

async def main():
    """Main application function"""
    try:
        # Setup signal handlers
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
        
        # Set global exception handler
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handle_exception)
        
        # Initialize services
        await initialize_services()
        
        # Start monitoring
        await start_monitoring()
        
        logger.info("FuseTester Fuse Monitoring System running successfully")
        
        # Keep the application running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            await shutdown()
            
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check Python version (require 3.9+)
    if sys.version_info < (3, 9):
        print("Python 3.9 or higher is required", file=sys.stderr)
        sys.exit(1)
    
    # Run the async main function
    asyncio.run(main())

"""
HTTP Data Sender Service
Sends fuse monitoring data to external server via HTTP POST requests
Includes fallback logic for offline operation on Pi 1 B+
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque
import requests
import os

logger = logging.getLogger(__name__)

class HTTPDataSender:
    """HTTP data transmission service with offline fallback"""
    
    def __init__(self):
        self.initialized = False
        self.server_url: Optional[str] = None
        self.api_key: Optional[str] = None
        self.timeout = 10  # seconds
        self.max_buffer_size = 100  # readings to keep in memory
        self.buffer = deque(maxlen=self.max_buffer_size)
        self.consecutive_failures = 0
        self.max_failures_before_buffer = 3
        self.send_lock = asyncio.Lock()
        self.last_successful_send = None
        
    async def initialize(self, options: Dict[str, Any] = None):
        """
        Initialize HTTP data sender
        
        Args:
            options: Configuration options (unused - uses environment)
        """
        if self.initialized:
            logger.info("HTTP Data Sender already initialized")
            return
        
        try:
            # Get configuration from environment
            self.server_url = os.getenv('SERVER_URL')
            self.api_key = os.getenv('API_KEY')
            self.timeout = int(os.getenv('HTTP_TIMEOUT', 10))
            self.max_buffer_size = int(os.getenv('MAX_BUFFER_SIZE', 100))
            
            if not self.server_url:
                raise ValueError("SERVER_URL environment variable is required")
            
            logger.info(f"Initializing HTTP Data Sender...")
            logger.info(f"Server URL: {self.server_url}")
            logger.info(f"Timeout: {self.timeout}s")
            logger.info(f"Buffer size: {self.max_buffer_size} readings")
            
            # Test connection
            await self._test_connection()
            
            self.initialized = True
            logger.info("HTTP Data Sender initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize HTTP Data Sender: {e}")
            # Don't raise - allow fallback to buffer mode
            self.initialized = True
            logger.warning("Running in buffer-only mode due to initialization failure")
    
    async def _test_connection(self):
        """Test connection to server"""
        try:
            headers = self._get_headers()
            
            # Simple health check or ping endpoint
            test_url = f"{self.server_url.rstrip('/')}/health"
            
            # Use requests in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(test_url, headers=headers, timeout=self.timeout)
            )
            
            if response.status_code < 400:
                logger.info("✓ Server connection test successful")
                return True
            else:
                logger.warning(f"Server returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Server connection test failed: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'FuseTester/1.0'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    async def log_fuse_readings(self, fuse_data: Dict[int, float]):
        """
        Send fuse readings to server with fallback logic
        
        Args:
            fuse_data: Dictionary mapping fuse numbers to voltage readings
        """
        if not self.initialized:
            raise RuntimeError("HTTP Data Sender not initialized")
        
        # Create data payload
        payload = {
            'timestamp': datetime.now().isoformat(),
            'device_id': os.getenv('DEVICE_ID', 'fusetester-001'),
            'readings': fuse_data,
            'system_info': await self._get_system_info()
        }
        
        async with self.send_lock:
            try:
                # Try to send current data
                success = await self._send_data(payload)
                
                if success:
                    self.consecutive_failures = 0
                    self.last_successful_send = datetime.now()
                    
                    # Try to send any buffered data
                    await self._send_buffered_data()
                    
                    logger.debug(f"Successfully sent fuse data ({len(fuse_data)} readings)")
                else:
                    # Add to buffer for retry
                    await self._buffer_data(payload)
                    
            except Exception as e:
                logger.error(f"Failed to send fuse data: {e}")
                await self._buffer_data(payload)
    
    async def _send_data(self, payload: Dict[str, Any]) -> bool:
        """
        Send single data payload to server
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.server_url:
                return False
            
            headers = self._get_headers()
            
            # Use requests in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    self.server_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
            )
            
            if response.status_code < 300:
                return True
            else:
                logger.warning(f"Server returned status {response.status_code}: {response.text}")
                self.consecutive_failures += 1
                return False
                
        except requests.exceptions.Timeout:
            logger.warning("HTTP request timed out")
            self.consecutive_failures += 1
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Connection to server failed")
            self.consecutive_failures += 1
            return False
        except Exception as e:
            logger.error(f"HTTP send error: {e}")
            self.consecutive_failures += 1
            return False
    
    async def _buffer_data(self, payload: Dict[str, Any]):
        """Add data to memory buffer"""
        self.buffer.append(payload)
        logger.warning(f"Data buffered ({len(self.buffer)}/{self.max_buffer_size}) - "
                      f"{self.consecutive_failures} consecutive failures")
        
        # Log warning if buffer is getting full
        if len(self.buffer) >= self.max_buffer_size * 0.8:
            logger.warning(f"Buffer nearly full: {len(self.buffer)}/{self.max_buffer_size}")
    
    async def _send_buffered_data(self):
        """Attempt to send buffered data"""
        if not self.buffer:
            return
        
        logger.info(f"Attempting to send {len(self.buffer)} buffered readings")
        
        # Send buffered data (oldest first)
        sent_count = 0
        while self.buffer and sent_count < 10:  # Limit batch size
            payload = self.buffer.popleft()
            
            success = await self._send_data(payload)
            if success:
                sent_count += 1
            else:
                # Put back and stop trying
                self.buffer.appendleft(payload)
                break
                
        if sent_count > 0:
            logger.info(f"Successfully sent {sent_count} buffered readings")
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system info to include with data"""
        try:
            import psutil
            
            return {
                'memory_percent': psutil.virtual_memory().percent,
                'cpu_temp': self._get_cpu_temp(),
                'uptime_seconds': psutil.boot_time()
            }
        except Exception:
            return {}
    
    def _get_cpu_temp(self) -> Optional[float]:
        """Get CPU temperature on Pi"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                return temp
        except Exception:
            return None
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current HTTP sender status
        
        Returns:
            Status dictionary
        """
        return {
            'initialized': self.initialized,
            'server_url': self.server_url,
            'buffer_count': len(self.buffer),
            'buffer_capacity': self.max_buffer_size,
            'consecutive_failures': self.consecutive_failures,
            'last_successful_send': self.last_successful_send.isoformat() if self.last_successful_send else None,
            'timeout': self.timeout
        }
    
    async def cleanup(self):
        """Cleanup HTTP sender resources"""
        try:
            if len(self.buffer) > 0:
                logger.warning(f"Shutting down with {len(self.buffer)} unsent readings in buffer")
            
            self.initialized = False
            logger.info("HTTP Data Sender cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during HTTP Data Sender cleanup: {e}")
    
    async def shutdown(self):
        """Shutdown HTTP sender service"""
        await self.cleanup()
    
    def is_initialized(self) -> bool:
        """Check if HTTP sender is initialized"""
        return self.initialized

# Alias for backwards compatibility
CSVLogger = HTTPDataSender

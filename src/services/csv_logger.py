"""
CSV Logger Service  
Handles CSV file creation, writing, and rotation
Optimized for Raspberry Pi 1 Model B+ with memory constraints
"""

import os
import csv
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import psutil

logger = logging.getLogger(__name__)

class CSVLogger:
    """CSV logging service with file rotation and memory optimization"""
    
    def __init__(self):
        self.initialized = False
        self.file_path: Optional[Path] = None
        self.file_handle: Optional[object] = None
        self.csv_writer: Optional[csv.DictWriter] = None
        self.file_size = 0
        self.max_file_size = 50 * 1024 * 1024  # 50MB default
        self.rotation_count = 0
        self.headers: Optional[List[str]] = None
        self.write_lock = asyncio.Lock()
    
    async def initialize(self, file_path: str, options: Dict[str, Any] = None):
        """
        Initialize CSV logger
        
        Args:
            file_path: Path to CSV file
            options: Configuration options
        """
        if self.initialized:
            logger.info("CSV logger already initialized")
            return
        
        try:
            options = options or {}
            
            self.file_path = Path(file_path).resolve()
            self.max_file_size = options.get('max_file_size', 
                                           int(os.getenv('CSV_MAX_FILE_SIZE', 50 * 1024 * 1024)))
            
            logger.info(f"Initializing CSV logger: {self.file_path}")
            logger.info(f"Max file size: {self.max_file_size / 1024 / 1024:.1f}MB")
            
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {self.file_path.parent}")
            
            # Check existing file size
            if self.file_path.exists():
                self.file_size = self.file_path.stat().st_size
                logger.info(f"Existing CSV file size: {self.file_size / 1024:.1f}KB")
            
            # Open file in append mode
            await self._open_file()
            
            self.initialized = True
            logger.info("CSV logger initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CSV logger: {e}")
            await self.cleanup()
            raise
    
    async def _open_file(self):
        """Open CSV file for writing"""
        try:
            self.file_handle = open(self.file_path, 'a', newline='', encoding='utf-8', buffering=8192)
            logger.debug(f"Opened CSV file: {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to open CSV file: {e}")
            raise
    
    async def write_headers(self, headers: List[str]):
        """
        Write CSV headers if file is new or empty
        
        Args:
            headers: List of header strings
        """
        if not self.initialized:
            raise RuntimeError("CSV logger not initialized")
        
        async with self.write_lock:
            try:
                self.headers = headers
                
                # Only write headers if file is new/empty
                if self.file_size == 0:
                    self.csv_writer = csv.DictWriter(self.file_handle, fieldnames=headers)
                    self.csv_writer.writeheader()
                    await self._flush_file()
                    
                    # Update file size
                    await self._update_file_size()
                    
                    logger.info(f"CSV headers written: {', '.join(headers)}")
                else:
                    # File exists, just create writer without writing headers
                    self.csv_writer = csv.DictWriter(self.file_handle, fieldnames=headers)
                    logger.info("CSV writer created for existing file")
                    
            except Exception as e:
                logger.error(f"Failed to write CSV headers: {e}")
                raise
    
    async def log_data(self, data: Union[Dict[str, Any], List[Any]]):
        """
        Log data to CSV file
        
        Args:
            data: Data to log (dict with key-value pairs or list of values)
        """
        if not self.initialized:
            raise RuntimeError("CSV logger not initialized")
        
        if not self.csv_writer:
            raise RuntimeError("CSV headers not set")
        
        async with self.write_lock:
            try:
                # Convert list to dict if necessary
                if isinstance(data, list):
                    if not self.headers:
                        raise RuntimeError("Headers must be set to use list data")
                    if len(data) != len(self.headers):
                        raise ValueError(f"Data length {len(data)} doesn't match headers length {len(self.headers)}")
                    data = dict(zip(self.headers, data))
                
                # Add timestamp if not present
                if 'timestamp' not in data and self.headers and 'timestamp' in self.headers:
                    data['timestamp'] = datetime.now().isoformat()
                
                # Write row
                self.csv_writer.writerow(data)
                
                # Update file size estimate
                estimated_row_size = len(','.join(str(v) for v in data.values())) + 1  # +1 for newline
                self.file_size += estimated_row_size
                
                # Periodic flush and size check
                if self.file_size % 1024 == 0:  # Every ~1KB
                    await self._flush_file()
                    
                    # Check if rotation is needed
                    if self.file_size >= self.max_file_size:
                        await self._rotate_file()
                
                logger.debug(f"Logged data: {len(data)} fields")
                
            except Exception as e:
                logger.error(f"Failed to log data to CSV: {e}")
                raise
    
    async def log_fuse_readings(self, fuse_data: Dict[int, float]):
        """
        Log fuse readings with proper formatting
        
        Args:
            fuse_data: Dictionary mapping fuse numbers to voltage readings
        """
        if not self.initialized:
            raise RuntimeError("CSV logger not initialized")
        
        try:
            # Create row data with timestamp
            row_data = {'timestamp': datetime.now().isoformat()}
            
            # Add fuse readings (ensure all 64 fuses are included)
            for fuse_num in range(1, 65):  # Fuses 1-64
                voltage = fuse_data.get(fuse_num, 0.0)
                row_data[f'fuse {fuse_num}'] = f"{voltage:.4f}"
            
            await self.log_data(row_data)
            
        except Exception as e:
            logger.error(f"Failed to log fuse readings: {e}")
            raise
    
    async def _flush_file(self):
        """Flush file buffer to disk"""
        try:
            if self.file_handle:
                self.file_handle.flush()
                os.fsync(self.file_handle.fileno())
        except Exception as e:
            logger.warning(f"Failed to flush CSV file: {e}")
    
    async def _update_file_size(self):
        """Update file size from disk"""
        try:
            if self.file_path and self.file_path.exists():
                self.file_size = self.file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Failed to update file size: {e}")
    
    async def _rotate_file(self):
        """Rotate CSV file when max size is reached"""
        try:
            logger.info(f"Rotating CSV file (size: {self.file_size / 1024 / 1024:.1f}MB)")
            
            # Close current file
            if self.file_handle:
                self.file_handle.close()
                self.file_handle = None
                self.csv_writer = None
            
            # Rename current file with rotation suffix
            self.rotation_count += 1
            rotated_path = self.file_path.with_suffix(f'.{self.rotation_count}.csv')
            self.file_path.rename(rotated_path)
            
            logger.info(f"Rotated file to: {rotated_path}")
            
            # Open new file
            self.file_size = 0
            await self._open_file()
            
            # Rewrite headers
            if self.headers:
                await self.write_headers(self.headers)
            
            logger.info("CSV file rotation complete")
            
        except Exception as e:
            logger.error(f"Failed to rotate CSV file: {e}")
            raise
    
    async def get_file_stats(self) -> Dict[str, Any]:
        """
        Get file statistics
        
        Returns:
            Dictionary with file stats
        """
        stats = {
            'file_path': str(self.file_path) if self.file_path else None,
            'file_size_bytes': self.file_size,
            'file_size_mb': self.file_size / 1024 / 1024,
            'rotation_count': self.rotation_count,
            'max_file_size_mb': self.max_file_size / 1024 / 1024
        }
        
        # Add disk space info
        try:
            if self.file_path:
                disk_usage = psutil.disk_usage(str(self.file_path.parent))
                stats['disk_free_mb'] = disk_usage.free / 1024 / 1024
                stats['disk_total_mb'] = disk_usage.total / 1024 / 1024
                stats['disk_used_percent'] = (disk_usage.used / disk_usage.total) * 100
        except Exception as e:
            logger.warning(f"Could not get disk stats: {e}")
            stats['disk_error'] = str(e)
        
        return stats
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current CSV logger status
        
        Returns:
            Status dictionary
        """
        status = {
            'initialized': self.initialized,
            'headers_count': len(self.headers) if self.headers else 0,
            'file_open': self.file_handle is not None
        }
        
        if self.initialized:
            status.update(await self.get_file_stats())
        
        return status
    
    async def cleanup(self):
        """Cleanup CSV logger resources"""
        try:
            if self.file_handle:
                logger.info("Closing CSV file...")
                await self._flush_file()
                self.file_handle.close()
                self.file_handle = None
            
            self.csv_writer = None
            self.initialized = False
            
            logger.info("CSV logger cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during CSV logger cleanup: {e}")
    
    async def shutdown(self):
        """Shutdown CSV logger service"""
        await self.cleanup()
    
    def is_initialized(self) -> bool:
        """Check if CSV logger is initialized"""
        return self.initialized

"""
Base Data Logger for BVEX Ground Station Widgets

Provides thread-safe CSV logging functionality for individual widget data types.
"""

import csv
import os
import time
import threading
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class WidgetDataLogger(ABC):
    """Base class for widget-specific data loggers"""
    
    def __init__(self, session_manager, data_type: str, headers: List[str]):
        """Initialize the widget data logger
        
        Args:
            session_manager: SessionManager instance
            data_type: Type of data being logged (e.g., 'gps', 'spectrometer')
            headers: List of CSV column headers
        """
        self.logger = logging.getLogger(f"{__name__}.{data_type}")
        self.session_manager = session_manager
        self.data_type = data_type
        self.headers = headers
        
        # Logging state
        self.is_logging = False
        self.csv_file = None
        self.csv_writer = None
        self.log_file_path = None
        
        # Thread control
        self.lock = threading.Lock()
        self.data_queue = []
        self.max_queue_size = 1000
        
        # Data rate tracking
        self.last_write_time = 0
        self.write_count = 0
        self.data_rate_hz = 1.0  # Default rate
        
    @abstractmethod
    def collect_data(self) -> Dict[str, Any]:
        """Collect data from the widget - to be implemented by subclasses"""
        pass
        
    def start_logging(self) -> bool:
        """Start logging data to CSV file"""
        if self.is_logging:
            self.logger.warning(f"{self.data_type} logging already active")
            return True
            
        try:
            # Get session path
            session_path = self.session_manager.get_current_session_path()
            if not session_path:
                raise RuntimeError("No active session")
                
            # Create CSV file path
            self.log_file_path = self.session_manager.get_csv_path(self.data_type)
            
            # Open CSV file for writing
            self.csv_file = open(self.log_file_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.headers)
            
            # Write headers
            self.csv_writer.writeheader()
            self.csv_file.flush()
            
            self.is_logging = True
            self.write_count = 0
            self.last_write_time = time.time()
            
            self.logger.info(f"Started {self.data_type} logging to {self.log_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start {self.data_type} logging: {e}")
            self._cleanup()
            return False
            
    def stop_logging(self) -> None:
        """Stop logging and close CSV file"""
        if not self.is_logging:
            return
            
        try:
            self.is_logging = False
            
            # Write any remaining queued data
            self._flush_queue()
            
            # Close file
            if self.csv_file:
                self.csv_file.close()
                self.logger.info(f"Stopped {self.data_type} logging - saved to {self.log_file_path}")
                
        except Exception as e:
            self.logger.error(f"Error stopping {self.data_type} logging: {e}")
        finally:
            self._cleanup()
            
    def log_data(self, data: Dict[str, Any]) -> bool:
        """Log a single data point
        
        Args:
            data: Dictionary of data to log
            
        Returns:
            True if data was logged successfully
        """
        if not self.is_logging or not self.csv_writer:
            return False
            
        try:
            # Add timestamp if not provided
            if 'timestamp' not in data:
                data['timestamp'] = time.time()
            if 'datetime_utc' not in data:
                data['datetime_utc'] = datetime.utcnow().isoformat() + 'Z'
                
            # Add data rate info
            data['update_rate_hz'] = self.data_rate_hz
            
            # Validate data against headers
            filtered_data = {k: data.get(k, '') for k in self.headers}
            
            # Thread-safe writing
            with self.lock:
                self.csv_writer.writerow(filtered_data)
                self.csv_file.flush()
                self.write_count += 1
                self.last_write_time = time.time()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging {self.data_type} data: {e}")
            return False
            
    def log_data_batch(self, data_list: List[Dict[str, Any]]) -> bool:
        """Log multiple data points at once
        
        Args:
            data_list: List of data dictionaries
            
        Returns:
            True if all data was logged successfully
        """
        if not self.is_logging or not self.csv_writer:
            return False
            
        try:
            with self.lock:
                for data in data_list:
                    # Add timestamps and rate info
                    if 'timestamp' not in data:
                        data['timestamp'] = time.time()
                    if 'datetime_utc' not in data:
                        data['datetime_utc'] = datetime.utcnow().isoformat() + 'Z'
                    data['update_rate_hz'] = self.data_rate_hz
                    
                    # Validate data
                    filtered_data = {k: data.get(k, '') for k in self.headers}
                    self.csv_writer.writerow(filtered_data)
                    
                self.csv_file.flush()
                self.write_count += len(data_list)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging {self.data_type} batch data: {e}")
            return False
            
    def update_data_rate(self, rate_hz: float) -> None:
        """Update the expected data rate
        
        Args:
            rate_hz: New data rate in Hz
        """
        self.data_rate_hz = max(0.1, rate_hz)  # Minimum 0.1 Hz
        
    def get_status(self) -> Dict[str, Any]:
        """Get current logging status
        
        Returns:
            Dictionary with logging status information
        """
        return {
            'data_type': self.data_type,
            'is_logging': self.is_logging,
            'log_file_path': self.log_file_path,
            'write_count': self.write_count,
            'data_rate_hz': self.data_rate_hz,
            'last_write_time': self.last_write_time
        }
        
    def get_log_file_size(self) -> Optional[int]:
        """Get current log file size in bytes"""
        if self.log_file_path and os.path.exists(self.log_file_path):
            return os.path.getsize(self.log_file_path)
        return None
        
    def _flush_queue(self) -> None:
        """Write any queued data to file"""
        if self.data_queue:
            self.log_data_batch(self.data_queue)
            self.data_queue.clear()
            
    def _cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.csv_file:
                self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            self.data_queue.clear()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.stop_logging()
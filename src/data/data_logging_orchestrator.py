"""
Data Logging Orchestrator for BVEX Ground Station

Central coordinator that manages all widget-specific loggers and provides
unified control over data logging operations.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from PyQt6.QtCore import QTimer, QObject

from src.data.session_manager import SessionManager
from src.data.widget_data_logger import WidgetDataLogger
from src.data.image_data_logger import ImageDataLogger


class DataLoggingOrchestrator(QObject):
    """Central manager for all data logging operations"""
    
    def __init__(self):
        super().__init__()
        """Initialize the data logging orchestrator"""
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.session_manager = SessionManager()
        self.loggers: Dict[str, WidgetDataLogger] = {}
        self.image_loggers: Dict[str, ImageDataLogger] = {}
        
        # State management
        self.is_logging = False
        self.current_session_path = None
        self.start_time = None
        
        # Thread control
        self.lock = threading.Lock()
        
        # Data polling timer
        self.polling_timer = None
        self.polling_interval_ms = 1000  # Poll every 1 second by default
        
    def register_logger(self, data_type: str, logger: WidgetDataLogger) -> None:
        """Register a widget data logger
        
        Args:
            data_type: Type of data (e.g., 'gps', 'spectrometer')
            logger: WidgetDataLogger instance
        """
        with self.lock:
            self.loggers[data_type] = logger
            self.logger.info(f"Registered {data_type} logger")
            
    def register_image_logger(self, image_type: str, logger: ImageDataLogger) -> None:
        """Register an image data logger
        
        Args:
            image_type: Type of images (e.g., 'star_camera')
            logger: ImageDataLogger instance
        """
        with self.lock:
            self.image_loggers[image_type] = logger
            self.logger.info(f"Registered {image_type} image logger")
            
    def start_logging(self, session_name: Optional[str] = None) -> bool:
        """Start data logging for all registered loggers
        
        Args:
            session_name: Optional custom session name
            
        Returns:
            True if logging started successfully
        """
        with self.lock:
            if self.is_logging:
                self.logger.warning("Data logging already active")
                return True
                
            try:
                # Create new session
                self.current_session_path = self.session_manager.create_session(session_name)
                self.start_time = datetime.now()
                
                # Start all loggers
                success_count = 0
                total_count = len(self.loggers) + len(self.image_loggers)
                
                for data_type, logger in self.loggers.items():
                    if logger.start_logging():
                        success_count += 1
                    else:
                        self.logger.error(f"Failed to start {data_type} logger")
                        
                for image_type, logger in self.image_loggers.items():
                    if logger.start_logging():
                        success_count += 1
                    else:
                        self.logger.error(f"Failed to start {image_type} image logger")
                        
                if success_count > 0:
                    self.is_logging = True
                    self.logger.info(
                        f"Started data logging session: {self.current_session_path} "
                        f"({success_count}/{total_count} loggers active)"
                    )
                    
                    # Start data polling
                    self.start_polling()
                    return True
                else:
                    self.logger.error("No loggers started successfully")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Failed to start data logging: {e}")
                return False
                
    def stop_logging(self) -> bool:
        """Stop data logging for all registered loggers"""
        with self.lock:
            if not self.is_logging:
                return True
                
            try:
                # Stop all loggers
                for data_type, logger in self.loggers.items():
                    logger.stop_logging()
                    
                for image_type, logger in self.image_loggers.items():
                    logger.stop_logging()
                    
                # Stop data polling
                self.stop_polling()
                    
                # Update session metadata
                if self.current_session_path:
                    duration = (datetime.now() - self.start_time).total_seconds()
                    self.session_manager.update_session_metadata({
                        'end_time': datetime.now().isoformat(),
                        'duration_seconds': duration,
                        'total_csv_files': len(self.loggers),
                        'total_image_types': len(self.image_loggers)
                    })
                    
                self.is_logging = False
                self.logger.info("Stopped data logging session")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping data logging: {e}")
                return False
                
    def log_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        """Log data for a specific type
        
        Args:
            data_type: Type of data to log
            data: Dictionary of data to log
            
        Returns:
            True if data was logged successfully
        """
        with self.lock:
            if not self.is_logging:
                return False
                
            logger = self.loggers.get(data_type)
            if logger:
                return logger.log_data(data)
            else:
                self.logger.warning(f"No logger registered for data type: {data_type}")
                return False
                
    def save_image(self, image_type: str, image_data: bytes, metadata: Dict[str, Any]) -> Optional[str]:
        """Save an image with metadata
        
        Args:
            image_type: Type of image (e.g., 'star_camera')
            image_data: Raw image bytes
            metadata: Dictionary with image metadata
            
        Returns:
            Path to saved image file, or None if failed/skipped
        """
        with self.lock:
            if not self.is_logging:
                return None
                
            logger = self.image_loggers.get(image_type)
            if logger:
                return logger.save_image(image_data, metadata)
            else:
                self.logger.warning(f"No image logger registered for type: {image_type}")
                return None
                
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive logging status
        
        Returns:
            Dictionary with complete logging status
        """
        with self.lock:
            status = {
                'is_logging': self.is_logging,
                'session_path': self.current_session_path,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'loggers': {},
                'image_loggers': {},
                'session_stats': {}
            }
            
            # Add logger statuses
            for data_type, logger in self.loggers.items():
                status['loggers'][data_type] = logger.get_status()
                
            for image_type, logger in self.image_loggers.items():
                status['image_loggers'][image_type] = logger.get_status()
                
            # Add session statistics
            if self.current_session_path:
                status['session_stats'] = self.session_manager.get_session_stats()
                
            return status
            
    def get_session_path(self) -> Optional[str]:
        """Get current session path"""
        with self.lock:
            return self.current_session_path
            
    def update_data_rate(self, data_type: str, rate_hz: float) -> bool:
        """Update data rate for a specific logger
        
        Args:
            data_type: Type of data
            rate_hz: New data rate in Hz
            
        Returns:
            True if rate was updated
        """
        with self.lock:
            logger = self.loggers.get(data_type)
            if logger:
                logger.update_data_rate(rate_hz)
                return True
            return False
            
    def list_available_loggers(self) -> Dict[str, List[str]]:
        """List all available loggers
        
        Returns:
            Dictionary with 'data' and 'image' logger types
        """
        return {
            'data': list(self.loggers.keys()),
            'image': list(self.image_loggers.keys())
        }
        
    def get_logger(self, data_type: str) -> Optional[WidgetDataLogger]:
        """Get a specific logger instance
        
        Args:
            data_type: Type of data
            
        Returns:
            WidgetDataLogger instance or None
        """
        return self.loggers.get(data_type)
        
    def get_image_logger(self, image_type: str) -> Optional[ImageDataLogger]:
        """Get a specific image logger instance
        
        Args:
            image_type: Type of images
            
        Returns:
            ImageDataLogger instance or None
        """
        return self.image_loggers.get(image_type)
        
    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old session directories
        
        Args:
            max_age_days: Maximum age in days to keep sessions
            
        Returns:
            Number of sessions cleaned up
        """
        return self.session_manager.cleanup_old_sessions(max_age_days)
        
    def list_sessions(self) -> list:
        """List all available sessions
        
        Returns:
            List of session directory paths
        """
        return self.session_manager.list_sessions()
        
    def is_logging_active(self) -> bool:
        """Check if logging is currently active"""
        return self.is_logging
        
    def start_polling(self) -> None:
        """Start automatic data polling from all registered loggers"""
        if self.polling_timer is None:
            self.polling_timer = QTimer()
            self.polling_timer.timeout.connect(self._poll_data)
            self.polling_timer.start(self.polling_interval_ms)
            self.logger.info("Started data polling")
            
    def stop_polling(self) -> None:
        """Stop automatic data polling"""
        if self.polling_timer:
            self.polling_timer.stop()
            self.polling_timer.deleteLater()
            self.polling_timer = None
            self.logger.info("Stopped data polling")
            
    def _poll_data(self) -> None:
        """Poll all registered loggers for new data"""
        if not self.is_logging:
            return
            
        try:
            for data_type, logger in self.loggers.items():
                try:
                    # Collect data from the widget
                    data = logger.collect_data()
                    if data:
                        # Handle both single dict and list of dicts
                        if isinstance(data, list):
                            # Handle list of data points (like spectra)
                            if data:
                                logger.log_data_batch(data)
                        elif isinstance(data, dict):
                            # Handle single data point
                            logger.log_data(data)
                except Exception as e:
                    self.logger.error(f"Error collecting data from {data_type} logger: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error during data polling: {e}")
            
    def set_polling_interval(self, interval_ms: int) -> None:
        """Set the polling interval in milliseconds
        
        Args:
            interval_ms: New polling interval in milliseconds
        """
        self.polling_interval_ms = max(100, interval_ms)  # Minimum 100ms
        if self.polling_timer and self.polling_timer.isActive():
            self.polling_timer.setInterval(self.polling_interval_ms)
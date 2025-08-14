"""
Backend Computer Data Logger for BVEX Ground Station

Logs Aquila backend computer status including CPU temperature, memory usage, and NVMe SSD storage.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class BackendDataLogger(WidgetDataLogger):
    """Logger for Aquila backend computer status data"""
    
    def __init__(self, session_manager: SessionManager, backend_widget):
        """Initialize backend data logger
        
        Args:
            session_manager: SessionManager instance
            backend_widget: BackendStatusWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            # CPU and memory
            'cpu_temp',
            'memory_percent',
            # SSD1 storage
            'ssd1_mounted',
            'ssd1_percent',
            'ssd1_used_gb',
            'ssd1_total_gb',
            # SSD2 storage
            'ssd2_mounted',
            'ssd2_percent',
            'ssd2_used_gb',
            'ssd2_total_gb',
            # Overall status
            'backend_connected',
            'update_rate_hz',
            'valid'
        ]
        
        super().__init__(session_manager, 'backend_status', headers)
        self.backend_widget = backend_widget
        
    def start_logging(self) -> bool:
        """Start logging and automatically activate the backend monitor widget
        
        Returns:
            True if logging started successfully
        """
        # Try to automatically activate the widget
        try:
            if hasattr(self.backend_widget, 'start_backend'):
                if not self.backend_widget.is_backend_active():
                    self.logger.info("Automatically activating backend monitor widget for data logging")
                    self.backend_widget.start_backend()
        except Exception as e:
            self.logger.warning(f"Could not automatically activate backend monitor widget: {e}")
            
        return super().start_logging()
    
    def stop_logging(self) -> bool:
        """Stop logging - widget remains active for user visibility
        
        Returns:
            True if logging stopped successfully
        """
        # Don't automatically stop the widget to maintain user control
        self.logger.info("Backend monitor widget remains active after data logging stops")
        return super().stop_logging()
    
    def collect_data(self) -> Dict[str, Any]:
        """Collect backend computer status data from widget
        
        Returns:
            Dictionary with backend status data, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.backend_widget, 'is_backend_active') or not self.backend_widget.is_backend_active():
                self.logger.debug("Backend monitor widget is not active, skipping data collection")
                return {}
                
            # Get current data from widget's Aquila client
            if hasattr(self.backend_widget, 'aquila_client'):
                current_data = self.backend_widget.aquila_client.current_data
            else:
                self.logger.debug("Backend widget has no aquila_client available")
                return {}
            
            # Only log when we have valid data
            if current_data and current_data.valid:
                # Calculate connection status
                backend_connected = self.backend_widget.aquila_client.is_connected()
                
                # Calculate update rate
                update_rate = 0.0
                try:
                    if hasattr(self.backend_widget, 'update_times') and len(self.backend_widget.update_times) >= 2:
                        recent_updates = [t for t in self.backend_widget.update_times 
                                        if (self.backend_widget.update_times[-1] - t).total_seconds() < 10]
                        if len(recent_updates) >= 2:
                            time_span = (recent_updates[-1] - recent_updates[0]).total_seconds()
                            if time_span > 0:
                                update_rate = (len(recent_updates) - 1) / time_span
                except Exception as e:
                    self.logger.debug(f"Could not calculate update rate: {e}")
                
                return {
                    # CPU and memory metrics
                    'cpu_temp': current_data.cpu_temp,
                    'memory_percent': current_data.memory_percent,
                    
                    # SSD1 metrics
                    'ssd1_mounted': current_data.ssd1_mounted,
                    'ssd1_percent': current_data.ssd1_percent,
                    'ssd1_used_gb': current_data.ssd1_used_gb,
                    'ssd1_total_gb': current_data.ssd1_total_gb,
                    
                    # SSD2 metrics
                    'ssd2_mounted': current_data.ssd2_mounted,
                    'ssd2_percent': current_data.ssd2_percent,
                    'ssd2_used_gb': current_data.ssd2_used_gb,
                    'ssd2_total_gb': current_data.ssd2_total_gb,
                    
                    # Overall status
                    'backend_connected': backend_connected,
                    'update_rate_hz': round(update_rate, 2),
                    'valid': current_data.valid
                }
            
            # No valid data to log
            self.logger.debug("Backend widget has no valid data available")
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting backend data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.backend_widget, 'update_timer') and self.backend_widget.update_timer:
                interval_ms = self.backend_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating backend data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current backend data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)

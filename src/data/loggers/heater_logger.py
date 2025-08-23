"""
Heater System Data Logger for BVEX Ground Station

Logs heater system telemetry data including relay states, temperatures, and current consumption.
Updated for display-only heater widget that uses telemetry interface.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class HeaterDataLogger(WidgetDataLogger):
    """Logger for heater system relay states and data"""
    
    def __init__(self, session_manager: SessionManager, heater_widget):
        """Initialize heater system data logger
        
        Args:
            session_manager: Session manager for file handling
            heater_widget: Reference to heater widget for data collection
        """
        # Define CSV headers for telemetry-based heater data
        headers = [
            'timestamp', 'datetime_utc', 'update_rate_hz',
            'starcam_state', 'motor_state', 'ethernet_state', 'lockpin_state', 'spare_state',
            'starcam_temp', 'motor_temp', 'ethernet_temp', 'lockpin_temp', 'spare_temp',
            'starcam_current', 'motor_current', 'ethernet_current', 'lockpin_current', 'spare_current',
            'total_current', 'system_running', 'valid'
        ]
        
        super().__init__(session_manager, 'heater_system', headers)
        self.heater_widget = heater_widget
        
    def start_logging(self) -> bool:
        """Start logging and automatically activate the heater widget
        
        Returns:
            True if logging started successfully
        """
        # Try to automatically activate the widget
        try:
            if hasattr(self.heater_widget, 'start_monitoring'):
                if not self.heater_widget.is_active:
                    self.logger.info("Automatically activating heater widget for data logging")
                    self.heater_widget.start_monitoring()
        except Exception as e:
            self.logger.warning(f"Could not automatically activate heater widget: {e}")
            
        return super().start_logging()
    
    def stop_logging(self) -> bool:
        """Stop logging - widget remains active for user visibility
        
        Returns:
            True if logging stopped successfully
        """
        # Don't automatically stop the widget to maintain user control
        self.logger.info("Heater widget remains active after data logging stops")
        return super().stop_logging()
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect heater system data from widget when active
        
        Returns:
            Dictionary with heater system states, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.heater_widget, 'is_active') or not self.heater_widget.is_active:
                return {}
                
            # Get current data from widget's heater client
            if hasattr(self.heater_widget, 'heater_client'):
                current_data = self.heater_widget.heater_client.get_current_data()
                
                if current_data and current_data.valid:
                    return {
                        'starcam_state': self._bool_to_int(current_data.starcam_state),
                        'motor_state': self._bool_to_int(current_data.motor_state),
                        'ethernet_state': self._bool_to_int(current_data.ethernet_state),
                        'lockpin_state': self._bool_to_int(current_data.lockpin_state),
                        'spare_state': self._bool_to_int(current_data.spare_state),
                        'starcam_temp': current_data.starcam_temp,
                        'motor_temp': current_data.motor_temp,
                        'ethernet_temp': current_data.ethernet_temp,
                        'lockpin_temp': current_data.lockpin_temp,
                        'spare_temp': current_data.spare_temp,
                        'starcam_current': current_data.starcam_current,
                        'motor_current': current_data.motor_current,
                        'ethernet_current': current_data.ethernet_current,
                        'lockpin_current': current_data.lockpin_current,
                        'spare_current': current_data.spare_current,
                        'total_current': current_data.total_current,
                        'system_running': self._bool_to_int(current_data.system_running),
                        'valid': current_data.valid
                    }
            
            # No valid data when widget is inactive
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting heater system data: {e}")
            return {}
            
    def _bool_to_int(self, value) -> int:
        """Convert boolean/None values to integers for logging
        
        Args:
            value: Boolean, None, or other value
            
        Returns:
            1 for True, 0 for False, -1 for None/Unknown
        """
        if value is True:
            return 1
        elif value is False:
            return 0
        else:
            return -1
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.heater_widget, 'update_timer') and self.heater_widget.update_timer:
                interval_ms = self.heater_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 0.5  # Default to 0.5 Hz
                self.data_rate_hz = rate_hz
        except Exception as e:
            self.logger.error(f"Error updating heater system data rate: {e}")
            self.data_rate_hz = 0.5  # Default fallback
            
    def log_current_data(self) -> bool:
        """Log current heater system data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)
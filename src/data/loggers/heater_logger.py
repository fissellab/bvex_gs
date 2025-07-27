"""
Heater System Data Logger for BVEX Ground Station

Logs heater system relay states and temperature data.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class HeaterDataLogger(WidgetDataLogger):
    """Logger for heater system relay states and data"""
    
    def __init__(self, session_manager: SessionManager, heater_widget):
        """Initialize heater system data logger
        
        Args:
            session_manager: SessionManager instance
            heater_widget: HeaterWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            'lockpin_state',
            'starcamera_state',
            'pv_state',
            'motor_state',
            'ethernet_state',
            'lockpin_temp',
            'starcamera_temp',
            'pv_temp',
            'motor_temp',
            'ethernet_temp',
            'valid'
        ]
        
        super().__init__(session_manager, 'heater_system', headers)
        self.heater_widget = heater_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect heater system data from widget when active
        
        Returns:
            Dictionary with heater system states, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.heater_widget, 'is_active') or not self.heater_widget.is_active:
                return {}
                
            # Get current data from widget
            current_data = self.heater_widget.current_data
            
            if current_data and current_data.valid:
                return {
                    'lockpin_state': self._bool_to_int(current_data.lockpin_state),
                    'starcamera_state': self._bool_to_int(current_data.starcamera_state),
                    'pv_state': self._bool_to_int(current_data.pv_state),
                    'motor_state': self._bool_to_int(current_data.motor_state),
                    'ethernet_state': self._bool_to_int(current_data.ethernet_state),
                    'lockpin_temp': current_data.lockpin_temp,
                    'starcamera_temp': current_data.starcamera_temp,
                    'pv_temp': current_data.pv_temp,
                    'motor_temp': current_data.motor_temp,
                    'ethernet_temp': current_data.ethernet_temp,
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
            if hasattr(self.heater_widget, 'update_timer'):
                interval_ms = self.heater_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating heater system data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current heater system data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)
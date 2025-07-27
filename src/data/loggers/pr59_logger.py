"""
PR59 Temperature Controller Data Logger for BVEX Ground Station

Logs PR59 temperature controller telemetry including temperatures and PID parameters.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class PR59DataLogger(WidgetDataLogger):
    """Logger for PR59 temperature controller data"""
    
    def __init__(self, session_manager: SessionManager, pr59_widget):
        """Initialize PR59 data logger
        
        Args:
            session_manager: SessionManager instance
            pr59_widget: PR59Widget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            'temperature',
            'fet_temperature',
            'current_ma',
            'voltage_mv',
            'kp',
            'ki',
            'kd',
            'setpoint',
            'valid'
        ]
        
        super().__init__(session_manager, 'pr59_temperature', headers)
        self.pr59_widget = pr59_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect PR59 temperature controller data from widget when active
        
        Returns:
            Dictionary with PR59 telemetry, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.pr59_widget, 'is_active') or not self.pr59_widget.is_active:
                return {}
                
            # Get current data from widget's PR59 client
            if hasattr(self.pr59_widget, 'pr59_client'):
                current_data = self.pr59_widget.pr59_client.current_data
            else:
                return {}
            
            if current_data and current_data.valid:
                return {
                    'temperature': current_data.temp,
                    'fet_temperature': current_data.fet_temp,
                    'current_ma': current_data.current * 1000,  # Convert to mA
                    'voltage_mv': current_data.voltage * 1000,  # Convert to mV
                    'kp': current_data.kp,
                    'ki': current_data.ki,
                    'kd': current_data.kd,
                    'setpoint': 0.0,  # Would need to be added to PR59Data
                    'valid': current_data.valid
                }
            
            # No valid data when widget is inactive
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting PR59 data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.pr59_widget, 'update_timer'):
                interval_ms = self.pr59_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating PR59 data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current PR59 data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)
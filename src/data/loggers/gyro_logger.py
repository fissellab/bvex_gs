"""
Gyro Data Logger for BVEX Ground Station

Logs gyroscope angular velocity data from the BCP Sag position sensor system,
including SPI gyro rates and system status.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class GyroDataLogger(WidgetDataLogger):
    """Logger for single-axis SPI gyroscope data from BCP Sag system"""
    
    def __init__(self, session_manager: SessionManager, gyro_widget):
        """Initialize Gyro data logger
        
        Args:
            session_manager: SessionManager instance
            gyro_widget: GyroWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            'spi_rate_deg_per_s',
            'pos_status',
            'pos_running',
            'connection_status',
            'consecutive_failures',
            'last_update_time',
            'connected',
            'valid',
            'update_rate_hz'
        ]
        
        super().__init__(session_manager, 'gyro', headers)
        self.gyro_widget = gyro_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect gyroscope data from widget when active
        
        Returns:
            Dictionary with gyro data, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.gyro_widget, 'is_active') or not self.gyro_widget.is_active:
                return {}
                
            # Get current gyro data from widget
            gyro_data = self.gyro_widget.last_gyro_data
            
            if not gyro_data:
                return {}
            
            # Get connection status
            connection_status = self.gyro_widget.gyro_client.get_connection_status()
            connected = self.gyro_widget.gyro_client.is_connected()
            consecutive_failures = self.gyro_widget.gyro_client.consecutive_failures
            
            return {
                'spi_rate_deg_per_s': gyro_data.spi_rate,
                'pos_status': gyro_data.pos_status,
                'pos_running': gyro_data.pos_running,
                'connection_status': connection_status,
                'consecutive_failures': consecutive_failures,
                'last_update_time': gyro_data.last_update_time,
                'connected': 1 if connected else 0,
                'valid': 1 if gyro_data.valid else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting gyro data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.gyro_widget, 'update_timer') and self.gyro_widget.update_timer:
                interval_ms = self.gyro_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
            elif hasattr(self.gyro_widget, 'update_frequency_hz'):
                # Use the frequency setting directly
                super().update_data_rate(float(self.gyro_widget.update_frequency_hz))
        except Exception as e:
            self.logger.error(f"Error updating gyro data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current gyro data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)

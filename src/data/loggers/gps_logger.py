"""
GPS Data Logger for BVEX Ground Station

Logs GPS coordinates, altitude, heading, speed, satellite count, and metadata from GPS widget.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager
from src.data.gps_client import GPSData


class GPSDataLogger(WidgetDataLogger):
    """Logger for GPS data including coordinates and metadata"""
    
    def __init__(self, session_manager: SessionManager, gps_widget):
        """Initialize GPS data logger
        
        Args:
            session_manager: SessionManager instance
            gps_widget: GPSDisplayWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            'lat',
            'lon',
            'alt',
            'head',
            'speed',
            'sats',
            'valid',
            'update_rate_hz'
        ]
        
        super().__init__(session_manager, 'gps', headers)
        self.gps_widget = gps_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect GPS data from widget when active
        
        Returns:
            Dictionary with GPS data, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.gps_widget, 'is_active') or not self.gps_widget.is_active:
                return {}
                
            # Get current GPS data from widget
            gps_data = self.gps_widget.last_gps_data
            
            return {
                'lat': gps_data.lat if gps_data.valid else 0.0,
                'lon': gps_data.lon if gps_data.valid else 0.0,
                'alt': gps_data.alt if gps_data.valid else 0.0,
                'head': gps_data.head if gps_data.valid else 0.0,
                'speed': gps_data.speed if gps_data.valid else 0.0,
                'sats': gps_data.sats if gps_data.valid else 0,
                'valid': gps_data.valid
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting GPS data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.gps_widget, 'update_timer'):
                interval_ms = self.gps_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating GPS data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current GPS data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)
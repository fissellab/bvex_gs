"""
TICC Data Logger for BVEX Ground Station

Logs TICC (Time Interval Counter) measurements including PPS drift, timing intervals,
and measurement metadata.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class TICCDataLogger(WidgetDataLogger):
    """Logger for TICC time interval measurements and status"""
    
    def __init__(self, session_manager: SessionManager, ticc_widget):
        """Initialize TICC data logger
        
        Args:
            session_manager: SessionManager instance
            ticc_widget: TICCWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            'ticc_timestamp',
            'interval_seconds',
            'interval_nanoseconds',
            'logging_status',
            'measurement_count',
            'current_file',
            'configured',
            'drift_rate_ns_per_s',
            'connected',
            'valid',
            'update_rate_hz'
        ]
        
        super().__init__(session_manager, 'ticc', headers)
        self.ticc_widget = ticc_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect TICC data from widget when active
        
        Returns:
            Dictionary with TICC measurement data, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.ticc_widget, 'is_active') or not self.ticc_widget.is_active:
                return {}
                
            # Get current TICC data from widget
            ticc_data = self.ticc_widget.current_data
            
            if not ticc_data or not ticc_data.valid:
                return {}
            
            # Calculate drift rate from plot widget if available
            drift_rate_ns_per_s = 0.0
            if hasattr(self.ticc_widget, 'plot_widget') and self.ticc_widget.plot_widget:
                drift_rate_ns_per_s = self.ticc_widget.plot_widget.latest_drift_rate * 1e9  # Convert s/s to ns/s
            
            # Check connection status
            connected = self.ticc_widget.ticc_client.is_connected()
            
            return {
                'ticc_timestamp': ticc_data.timestamp,
                'interval_seconds': ticc_data.interval,
                'interval_nanoseconds': ticc_data.interval * 1e9,  # Convert to nanoseconds for easier reading
                'logging_status': 1 if ticc_data.logging else 0,
                'measurement_count': ticc_data.measurement_count,
                'current_file': ticc_data.current_file,
                'configured': 1 if ticc_data.configured else 0,
                'drift_rate_ns_per_s': drift_rate_ns_per_s,
                'connected': 1 if connected else 0,
                'valid': 1 if ticc_data.valid else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting TICC data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.ticc_widget, 'update_timer') and self.ticc_widget.update_timer:
                interval_ms = self.ticc_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating TICC data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current TICC data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)

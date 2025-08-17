"""
BCP Housekeeping Data Logger for BVEX Ground Station

Logs BCP housekeeping sensor data including temperatures, pressure, and system status.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class HousekeepingDataLogger(WidgetDataLogger):
    """Logger for BCP housekeeping sensor data"""
    
    def __init__(self, session_manager: SessionManager, housekeeping_widget):
        """Initialize housekeeping data logger
        
        Args:
            session_manager: SessionManager instance
            housekeeping_widget: HousekeepingWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            # System Status
            'hk_powered',
            'hk_running',
            # Temperature Sensors (°C)
            'hk_ocxo_temp',
            'hk_ifamp_temp',
            'hk_lo_temp',
            'hk_tec_temp',
            'hk_backend_chassis_temp',
            'hk_nic_temp',
            'hk_rfsoc_chassis_temp',
            'hk_rfsoc_chip_temp',
            'hk_lna1_temp',
            'hk_lna2_temp',
            # Pressure Sensor (bar)
            'hk_pv_pressure_bar',
            # Data validity
            'valid'
        ]
        
        super().__init__(session_manager, 'bcp_housekeeping', headers)
        self.housekeeping_widget = housekeeping_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect BCP housekeeping data from widget when active
        
        Returns:
            Dictionary with housekeeping telemetry, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.housekeeping_widget, 'is_active') or not self.housekeeping_widget.is_active:
                return {}
                
            # Get current data from widget's housekeeping client
            if hasattr(self.housekeeping_widget, 'housekeeping_client'):
                current_data = self.housekeeping_widget.housekeeping_client.current_data
            else:
                return {}
            
            if current_data and current_data.valid:
                return {
                    # System Status
                    'hk_powered': current_data.hk_powered,
                    'hk_running': current_data.hk_running,
                    
                    # Temperature Sensors (°C)
                    'hk_ocxo_temp': current_data.hk_ocxo_temp,
                    'hk_ifamp_temp': current_data.hk_ifamp_temp,
                    'hk_lo_temp': current_data.hk_lo_temp,
                    'hk_tec_temp': current_data.hk_tec_temp,
                    'hk_backend_chassis_temp': current_data.hk_backend_chassis_temp,
                    'hk_nic_temp': current_data.hk_nic_temp,
                    'hk_rfsoc_chassis_temp': current_data.hk_rfsoc_chassis_temp,
                    'hk_rfsoc_chip_temp': current_data.hk_rfsoc_chip_temp,
                    'hk_lna1_temp': current_data.hk_lna1_temp,
                    'hk_lna2_temp': current_data.hk_lna2_temp,
                    
                    # Pressure Sensor (bar)
                    'hk_pv_pressure_bar': current_data.hk_pv_pressure_bar,
                    
                    # Data validity
                    'valid': current_data.valid
                }
            
            # No valid data when widget is inactive
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting housekeeping data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget (housekeeping updates every 2 seconds by default)
            if hasattr(self.housekeeping_widget, 'update_timer'):
                interval_ms = self.housekeeping_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 0.5  # Default 0.5 Hz
                super().update_data_rate(rate_hz)
            else:
                # Default to 0.5 Hz (every 2 seconds) if timer not available
                super().update_data_rate(0.5)
        except Exception as e:
            self.logger.error(f"Error updating housekeeping data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current housekeeping data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)

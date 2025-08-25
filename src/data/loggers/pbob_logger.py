"""
PBoB (Power Distribution Box) Data Logger for BVEX Ground Station

Logs relay states and current measurements for all subsystems from PBoB widget.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class PBoBDataLogger(WidgetDataLogger):
    """Logger for PBoB relay states and current measurements"""
    
    def __init__(self, session_manager: SessionManager, pbob_widget):
        """Initialize PBoB data logger
        
        Args:
            session_manager: SessionManager instance
            pbob_widget: PBoBWidget instance
        """
        headers = [
            'timestamp',
            'star_camera_state',
            'star_camera_current',
            'motor_state',
            'motor_current',
            'gps_state',
            'gps_current',
            'lock_pin_state',
            'lock_pin_current',
            'lna_state',
            'lna_current',
            'mixer_state',
            'mixer_current',
            'rfsoc_state',
            'rfsoc_current',
            'timing_state',
            'timing_current',
            'heater_state',
            'heater_current',
            'position_state',
            'position_current',
            'housekeeping_state',
            'housekeeping_current',
            'valid'
        ]
        
        super().__init__(session_manager, 'pbob', headers)
        self.pbob_widget = pbob_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect PBoB relay states and current measurements from widget when active
        
        Returns:
            Dictionary with PBoB telemetry, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.pbob_widget, 'is_active') or not self.pbob_widget.is_active:
                return {}
                
            # Get current data from OphClient
            if hasattr(self.pbob_widget, 'oph_client'):
                data = self.pbob_widget.oph_client.get_data()
                
                if data and data.valid:
                    return {
                        'star_camera_state': data.sc_state,
                        'star_camera_current': data.sc_curr,
                        'motor_state': data.m_state,
                        'motor_current': data.m_curr,
                        'gps_state': data.gps_state,
                        'gps_current': data.gps_curr,
                        'lock_pin_state': data.lp_state,
                        'lock_pin_current': data.lp_curr,
                        'lna_state': data.lna_state,
                        'lna_current': data.lna_curr,
                        'mixer_state': data.mix_state,
                        'mixer_current': data.mix_curr,
                        'rfsoc_state': data.rfsoc_state,
                        'rfsoc_current': data.rfsoc_curr,
                        'timing_state': data.timing_state,
                        'timing_current': data.timing_curr,
                        'heater_state': data.heat_state,
                        'heater_current': data.heat_curr,
                        'position_state': data.pos_state,
                        'position_current': data.pos_curr,
                        'housekeeping_state': data.hk_state,
                        'housekeeping_current': data.hk_curr,
                        'valid': data.valid
                    }
            
            # No valid data when widget is inactive
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting PBoB data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.pbob_widget, 'update_timer'):
                interval_ms = self.pbob_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating PBoB data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current PBoB telemetry data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)
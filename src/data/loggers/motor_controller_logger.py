"""
Motor Controller Data Logger for BVEX Ground Station

Logs motor controller telemetry including positions, velocities, and temperatures.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class MotorControllerDataLogger(WidgetDataLogger):
    """Logger for motor controller telemetry data"""
    
    def __init__(self, session_manager: SessionManager, motor_widget):
        """Initialize motor controller data logger
        
        Args:
            session_manager: SessionManager instance
            motor_widget: MotorControllerWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            'current_position',
            'current_velocity',
            'temperature',
            'axis_mode',
            'target_position',
            'target_velocity',
            'operation_type',
            'motor_current',
            'switch_status',
            'limit_flags',
            'position_encoder',
            'update_rate_hz'
        ]
        
        super().__init__(session_manager, 'motor_controller', headers)
        self.motor_widget = motor_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect motor controller data from widget when active
        
        Returns:
            Dictionary with motor controller telemetry, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.motor_widget, 'is_active') or not self.motor_widget.is_active:
                return {}
                
            # Get current telemetry from widget
            if hasattr(self.motor_widget, 'get_current_telemetry'):
                telemetry = self.motor_widget.get_current_telemetry()
                if telemetry and telemetry.valid:
                    return {
                        'current_position': telemetry.mc_pos,
                        'current_velocity': telemetry.mc_vel,
                        'temperature': telemetry.mc_temp,
                        'axis_mode': telemetry.ax_mode,
                        'target_position': telemetry.ax_dest,
                        'target_velocity': telemetry.ax_vel,
                        'operation_type': telemetry.ax_ot,
                        'motor_current': telemetry.mc_curr,
                        'switch_status': telemetry.mc_sw,
                        'limit_flags': telemetry.mc_lf,
                        'position_encoder': telemetry.mc_sr
                    }
            
            # Fallback to basic data
            current_data = self.motor_widget.current_telemetry
            if current_data and current_data.valid:
                return {
                    'current_position': current_data.mc_pos,
                    'current_velocity': current_data.mc_vel,
                    'temperature': current_data.mc_temp,
                    'axis_mode': current_data.ax_mode,
                    'target_position': current_data.ax_dest,
                    'target_velocity': current_data.ax_vel,
                    'operation_type': current_data.ax_ot,
                    'motor_current': current_data.mc_curr,
                    'switch_status': current_data.mc_sw,
                    'limit_flags': current_data.mc_lf,
                    'position_encoder': current_data.mc_sr
                }
                
            # No valid data when widget is inactive
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting motor controller data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.motor_widget, 'update_frequency_hz'):
                rate_hz = self.motor_widget.update_frequency_hz
                super().update_data_rate(rate_hz)
            elif hasattr(self.motor_widget, 'update_timer'):
                interval_ms = self.motor_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating motor controller data rate: {e}")
            
    def log_current_data(self) -> bool:
        """Log current motor controller data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)
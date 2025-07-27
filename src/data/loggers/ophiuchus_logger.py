"""
Ophiuchus Telemetry Data Logger for BVEX Ground Station

Logs comprehensive telemetry data from the Ophiuchus server including
star camera, motor controller, and scanning operations data.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class OphiuchusDataLogger(WidgetDataLogger):
    """Logger for comprehensive Ophiuchus telemetry data"""
    
    def __init__(self, session_manager: SessionManager, source_widget):
        """Initialize Ophiuchus telemetry logger
        
        Args:
            session_manager: SessionManager instance
            source_widget: Widget that provides Ophiuchus telemetry (star_camera, motor_controller, or scanning_operations)
        """
        headers = [
            'timestamp',
            'datetime_utc',
            # Star Camera Data
            'sc_ra',
            'sc_dec',
            'sc_fr',
            'sc_ir',
            'sc_az',
            'sc_alt',
            'sc_texp',
            'sc_start_focus',
            'sc_end_focus',
            'sc_curr_focus',
            'sc_focus_step',
            'sc_focus_mode',
            'sc_solve',
            'sc_save',
            # Motor Controller Data
            'mc_curr',
            'mc_sw',
            'mc_lf',
            'mc_sr',
            'mc_pos',
            'mc_temp',
            'mc_vel',
            'mc_cwr',
            'mc_cww',
            'mc_np',
            'mc_pt',
            'mc_it',
            'mc_dt',
            # Axis Operation Data
            'ax_mode',
            'ax_dest',
            'ax_vel',
            'ax_dest_az',
            'ax_vel_az',
            'ax_ot',
            # Scanning Operation Data
            'scan_mode',
            'scan_start',
            'scan_stop',
            'scan_vel',
            'scan_scan',
            'scan_nscans',
            'scan_offset',
            'scan_op',
            # Target Coordinates
            'target_lon',
            'target_lat',
            'target_type',
            'valid'
        ]
        
        super().__init__(session_manager, 'ophiuchus', headers)
        self.source_widget = source_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect comprehensive Ophiuchus telemetry data when widget is active
        
        Returns:
            Dictionary with complete Ophiuchus telemetry, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.source_widget, 'is_active') or not self.source_widget.is_active:
                return {}
                
            # Get telemetry from the source widget
            if hasattr(self.source_widget, 'get_current_telemetry'):
                telemetry = self.source_widget.get_current_telemetry()
                if telemetry and telemetry.valid:
                    return {
                        # Star Camera Data
                        'sc_ra': telemetry.sc_ra,
                        'sc_dec': telemetry.sc_dec,
                        'sc_fr': telemetry.sc_fr,
                        'sc_ir': telemetry.sc_ir,
                        'sc_az': telemetry.sc_az,
                        'sc_alt': telemetry.sc_alt,
                        'sc_texp': telemetry.sc_texp,
                        'sc_start_focus': telemetry.sc_start_focus,
                        'sc_end_focus': telemetry.sc_end_focus,
                        'sc_curr_focus': telemetry.sc_curr_focus,
                        'sc_focus_step': telemetry.sc_focus_step,
                        'sc_focus_mode': telemetry.sc_focus_mode,
                        'sc_solve': telemetry.sc_solve,
                        'sc_save': telemetry.sc_save,
                        # Motor Controller Data
                        'mc_curr': telemetry.mc_curr,
                        'mc_sw': telemetry.mc_sw,
                        'mc_lf': telemetry.mc_lf,
                        'mc_sr': telemetry.mc_sr,
                        'mc_pos': telemetry.mc_pos,
                        'mc_temp': telemetry.mc_temp,
                        'mc_vel': telemetry.mc_vel,
                        'mc_cwr': telemetry.mc_cwr,
                        'mc_cww': telemetry.mc_cww,
                        'mc_np': telemetry.mc_np,
                        'mc_pt': telemetry.mc_pt,
                        'mc_it': telemetry.mc_it,
                        'mc_dt': telemetry.mc_dt,
                        # Axis Operation Data
                        'ax_mode': telemetry.ax_mode,
                        'ax_dest': telemetry.ax_dest,
                        'ax_vel': telemetry.ax_vel,
                        'ax_dest_az': telemetry.ax_dest_az,
                        'ax_vel_az': telemetry.ax_vel_az,
                        'ax_ot': telemetry.ax_ot,
                        # Scanning Operation Data
                        'scan_mode': telemetry.scan_mode,
                        'scan_start': telemetry.scan_start,
                        'scan_stop': telemetry.scan_stop,
                        'scan_vel': telemetry.scan_vel,
                        'scan_scan': telemetry.scan_scan,
                        'scan_nscans': telemetry.scan_nscans,
                        'scan_offset': telemetry.scan_offset,
                        'scan_op': telemetry.scan_op,
                        # Target Coordinates
                        'target_lon': telemetry.target_lon,
                        'target_lat': telemetry.target_lat,
                        'target_type': telemetry.target_type,
                        'valid': telemetry.valid
                    }
            
            # No valid data when widget is inactive
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting Ophiuchus data: {e}")
            return {}
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Get default data structure with zero/empty values"""
        return {
            # Star Camera Data
            'sc_ra': 0.0,
            'sc_dec': 0.0,
            'sc_fr': 0.0,
            'sc_ir': 0.0,
            'sc_az': 0.0,
            'sc_alt': 0.0,
            'sc_texp': 0.0,
            'sc_start_focus': 0,
            'sc_end_focus': 0,
            'sc_curr_focus': 0,
            'sc_focus_step': 0,
            'sc_focus_mode': 0,
            'sc_solve': 0,
            'sc_save': 0,
            # Motor Controller Data
            'mc_curr': 0.0,
            'mc_sw': 0,
            'mc_lf': 0,
            'mc_sr': 0,
            'mc_pos': 0.0,
            'mc_temp': 0.0,
            'mc_vel': 0.0,
            'mc_cwr': 0,
            'mc_cww': 0,
            'mc_np': 0,
            'mc_pt': 0,
            'mc_it': 0,
            'mc_dt': 0,
            # Axis Operation Data
            'ax_mode': 0,
            'ax_dest': 0.0,
            'ax_vel': 0.0,
            'ax_dest_az': 0.0,
            'ax_vel_az': 0.0,
            'ax_ot': 0,
            # Scanning Operation Data
            'scan_mode': 0,
            'scan_start': 0.0,
            'scan_stop': 0.0,
            'scan_vel': 0.0,
            'scan_scan': 0,
            'scan_nscans': 0,
            'scan_offset': 0.0,
            'scan_op': 0,
            # Target Coordinates
            'target_lon': 0.0,
            'target_lat': 0.0,
            'target_type': 'None',
            'valid': False
        }
    
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from source widget
            if hasattr(self.source_widget, 'update_timer'):
                interval_ms = self.source_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating Ophiuchus data rate: {e}")
    
    def log_current_data(self) -> bool:
        """Log current Ophiuchus telemetry data
        
        Returns:
            True if data was logged successfully
        """
        data = self.collect_data()
        return self.log_data(data)
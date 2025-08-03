"""
System Monitor Data Logger for BVEX Ground Station

Logs system metrics (CPU temperature, memory usage, storage) from both flight computers.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager


class SystemMonitorDataLogger(WidgetDataLogger):
    """Logger for system monitor data from both flight computers"""
    
    def __init__(self, session_manager: SessionManager, system_monitor_widget):
        """Initialize system monitor data logger
        
        Args:
            session_manager: SessionManager instance
            system_monitor_widget: SystemMonitorWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            # Ophiuchus system data
            'oph_cpu_temp',
            'oph_cpu_usage',
            'oph_mem_used_str',
            'oph_mem_total_str',
            'oph_mem_used_bytes',
            'oph_mem_total_bytes',
            'oph_ssd_used',
            'oph_ssd_total',
            'oph_ssd_mounted',
            'oph_valid',
            # Saggitarius system data
            'sag_cpu_temp',
            'sag_cpu_usage',
            'sag_mem_used_str',
            'sag_mem_total_str',
            'sag_mem_used_bytes',
            'sag_mem_total_bytes',
            'sag_ssd_used',
            'sag_ssd_total',
            'sag_ssd_mounted',
            'sag_valid',
            # Overall status
            'systems_connected',
            'update_rate_hz'
        ]
        
        super().__init__(session_manager, 'system_monitor', headers)
        self.system_monitor_widget = system_monitor_widget
        
    def start_logging(self) -> bool:
        """Start logging and automatically activate the system monitor widget
        
        Returns:
            True if logging started successfully
        """
        # Try to automatically activate the widget
        try:
            if hasattr(self.system_monitor_widget, 'start_monitoring'):
                if not self.system_monitor_widget.is_active:
                    self.logger.info("Automatically activating system monitor widget for data logging")
                    self.system_monitor_widget.start_monitoring()
        except Exception as e:
            self.logger.warning(f"Could not automatically activate system monitor widget: {e}")
            
        return super().start_logging()
    
    def stop_logging(self) -> bool:
        """Stop logging - widget remains active for user visibility
        
        Returns:
            True if logging stopped successfully
        """
        # Don't automatically stop the widget to maintain user control
        self.logger.info("System monitor widget remains active after data logging stops")
        return super().stop_logging()
    
    def collect_data(self) -> Dict[str, Any]:
        """Collect system monitor data from widget
        
        Returns:
            Dictionary with system monitor data, includes placeholder data if widget is inactive
        """
        try:
            # Check if widget is active - if not, return placeholder data
            if not hasattr(self.system_monitor_widget, 'is_active') or not self.system_monitor_widget.is_active:
                self.logger.debug("System monitor widget is not active, returning placeholder data")
                # Return placeholder data with all systems marked as invalid
                return {
                    'oph_cpu_temp': None,
                    'oph_cpu_usage': None,
                    'oph_mem_used_str': None,
                    'oph_mem_total_str': None,
                    'oph_mem_used_bytes': None,
                    'oph_mem_total_bytes': None,
                    'oph_ssd_used': None,
                    'oph_ssd_total': None,
                    'oph_ssd_mounted': None,
                    'oph_valid': False,
                    'sag_cpu_temp': None,
                    'sag_cpu_usage': None,
                    'sag_mem_used_str': None,
                    'sag_mem_total_str': None,
                    'sag_mem_used_bytes': None,
                    'sag_mem_total_bytes': None,
                    'sag_ssd_used': None,
                    'sag_ssd_total': None,
                    'sag_ssd_mounted': None,
                    'sag_valid': False,
                    'systems_connected': 0,
                    'update_rate_hz': 0.0
                }
                
            # Get current system data from widget
            system_data = getattr(self.system_monitor_widget, 'system_data', {})
            
            if not system_data:
                self.logger.debug("System monitor widget has no system_data available")
                return {
                    'oph_cpu_temp': None,
                    'oph_cpu_usage': None,
                    'oph_mem_used_str': None,
                    'oph_mem_total_str': None,
                    'oph_mem_used_bytes': None,
                    'oph_mem_total_bytes': None,
                    'oph_ssd_used': None,
                    'oph_ssd_total': None,
                    'oph_ssd_mounted': None,
                    'oph_valid': False,
                    'sag_cpu_temp': None,
                    'sag_cpu_usage': None,
                    'sag_mem_used_str': None,
                    'sag_mem_total_str': None,
                    'sag_mem_used_bytes': None,
                    'sag_mem_total_bytes': None,
                    'sag_ssd_used': None,
                    'sag_ssd_total': None,
                    'sag_ssd_mounted': None,
                    'sag_valid': False,
                    'systems_connected': 0,
                    'update_rate_hz': 0.0
                }
            
            # Extract Ophiuchus data
            oph_data = system_data.get('ophiuchus')
            sag_data = system_data.get('saggitarius')
            
            # Build data row (timestamps will be added automatically by base class)
            data = {}
            
            # Ophiuchus system metrics
            if oph_data:
                data.update({
                    'oph_cpu_temp': oph_data.cpu_temp if oph_data.valid else None,
                    'oph_cpu_usage': oph_data.cpu_usage if oph_data.valid else None,
                    'oph_mem_used_str': oph_data.mem_used_str if oph_data.valid else None,
                    'oph_mem_total_str': oph_data.mem_total_str if oph_data.valid else None,
                    'oph_mem_used_bytes': oph_data.mem_used_bytes if oph_data.valid else None,
                    'oph_mem_total_bytes': oph_data.mem_total_bytes if oph_data.valid else None,
                    'oph_ssd_used': oph_data.ssd_used if oph_data.valid else None,
                    'oph_ssd_total': oph_data.ssd_total if oph_data.valid else None,
                    'oph_ssd_mounted': oph_data.ssd_mounted if oph_data.valid else None,
                    'oph_valid': oph_data.valid,
                })
            else:
                data.update({
                    'oph_cpu_temp': None,
                    'oph_cpu_usage': None,
                    'oph_mem_used_str': None,
                    'oph_mem_total_str': None,
                    'oph_mem_used_bytes': None,
                    'oph_mem_total_bytes': None,
                    'oph_ssd_used': None,
                    'oph_ssd_total': None,
                    'oph_ssd_mounted': None,
                    'oph_valid': False,
                })
            
            # Saggitarius system metrics
            if sag_data:
                data.update({
                    'sag_cpu_temp': sag_data.cpu_temp if sag_data.valid else None,
                    'sag_cpu_usage': sag_data.cpu_usage if sag_data.valid else None,
                    'sag_mem_used_str': sag_data.mem_used_str if sag_data.valid else None,
                    'sag_mem_total_str': sag_data.mem_total_str if sag_data.valid else None,
                    'sag_mem_used_bytes': sag_data.mem_used_bytes if sag_data.valid else None,
                    'sag_mem_total_bytes': sag_data.mem_total_bytes if sag_data.valid else None,
                    'sag_ssd_used': sag_data.ssd_used if sag_data.valid else None,
                    'sag_ssd_total': sag_data.ssd_total if sag_data.valid else None,
                    'sag_ssd_mounted': sag_data.ssd_mounted if sag_data.valid else None,
                    'sag_valid': sag_data.valid,
                })
            else:
                data.update({
                    'sag_cpu_temp': None,
                    'sag_cpu_usage': None,
                    'sag_mem_used_str': None,
                    'sag_mem_total_str': None,
                    'sag_mem_used_bytes': None,
                    'sag_mem_total_bytes': None,
                    'sag_ssd_used': None,
                    'sag_ssd_total': None,
                    'sag_ssd_mounted': None,
                    'sag_valid': False,
                })
            
            # Overall status
            systems_connected = 0
            if oph_data and oph_data.valid:
                systems_connected += 1
            if sag_data and sag_data.valid:
                systems_connected += 1
                
            data['systems_connected'] = systems_connected
            
            self.logger.debug(f"Successfully collected system monitor data: {systems_connected} systems connected")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting system monitor data: {e}")
            return {}
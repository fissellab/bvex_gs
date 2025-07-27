"""
Spectrometer Data Logger for BVEX Ground Station

Logs complete 2048-point spectrometer data with timestamps in single row format.
"""

from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.session_manager import SessionManager
import time


class SpectrometerDataLogger(WidgetDataLogger):
    """Logger for complete 2048-point spectrometer data in single row format"""
    
    def __init__(self, session_manager: SessionManager, spectrometer_widget):
        """Initialize spectrometer data logger
        
        Args:
            session_manager: SessionManager instance
            spectrometer_widget: SpectraDisplayWidget instance
        """
        # Minimal headers: just timestamp and 2048 data columns
        headers = ['timestamp'] + [f'data_{i}' for i in range(2048)]
        
        super().__init__(session_manager, 'spectrometer', headers)
        self.spectrometer_widget = spectrometer_widget
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect complete spectrometer data in single row format
        
        Returns:
            Dictionary with timestamp and 2048 power values in one row
        """
        try:
            # Check if widget is active
            if not hasattr(self.spectrometer_widget, 'is_active') or not self.spectrometer_widget.is_active:
                return {}
                
            # Get current spectrum data from widget
            spectrum_data = self.spectrometer_widget.spectrum_data
            
            if not spectrum_data or not spectrum_data.valid:
                return {}
            
            # Ensure we have exactly 2048 points
            if len(spectrum_data.data) != 2048:
                self.logger.warning(f"Expected 2048 points, got {len(spectrum_data.data)}, padding with zeros")
                
            # Create single row with all 2048 points
            current_time = time.time()
            datetime_utc = str(time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(current_time))) + 'Z'
            
            # Build data row with just timestamp and 2048 data values
            data_row = {'timestamp': spectrum_data.timestamp}  # Use server timestamp
            
            # Add all 2048 spectra values
            for i, value in enumerate(spectrum_data.data):
                data_row[f'data_{i}'] = value
                
            # Pad with zeros if we have fewer than 2048 points
            for i in range(len(spectrum_data.data), 2048):
                data_row[f'data_{i}'] = 0.0
                
            return data_row
            
        except Exception as e:
            self.logger.error(f"Error collecting spectrometer data: {e}")
            return {}
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.spectrometer_widget, 'update_timer'):
                interval_ms = self.spectrometer_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating spectrometer data rate: {e}")
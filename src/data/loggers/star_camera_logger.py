"""
Star Camera Data Logger for BVEX Ground Station

Logs star camera telemetry and saves images with metadata.
"""

import os
from typing import Dict, Any, Optional
from src.data.widget_data_logger import WidgetDataLogger
from src.data.image_data_logger import ImageDataLogger
from src.data.session_manager import SessionManager


class StarCameraDataLogger(WidgetDataLogger):
    """Logger for star camera telemetry and metadata"""
    
    def __init__(self, session_manager: SessionManager, star_camera_widget):
        """Initialize star camera data logger
        
        Args:
            session_manager: SessionManager instance
            star_camera_widget: StarCameraWidget instance
        """
        headers = [
            'timestamp',
            'datetime_utc',
            'ra',
            'dec',
            'field_rotation',
            'image_rotation',
            'azimuth',
            'altitude',
            'exposure_time',
            'focus_position',
            'auto_focus_start',
            'auto_focus_end',
            'focus_step',
            'focus_mode',
            'solve_status',
            'save_status',
            'image_filename',
            'image_valid',
            'update_rate_hz'
        ]
        
        super().__init__(session_manager, 'star_camera', headers)
        self.star_camera_widget = star_camera_widget
        
        # Image logger for saving actual images
        self.image_logger = ImageDataLogger(session_manager, 'star_camera')
        
        # Configure image logger for 100% quality and no rate limiting
        self.image_logger.configure(quality=100, rate_limit=1)
        
    def collect_data(self) -> Dict[str, Any]:
        """Collect star camera telemetry from widget when active
        
        Returns:
            Dictionary with star camera telemetry, empty dict if widget is inactive
        """
        try:
            # Check if widget is active
            if not hasattr(self.star_camera_widget, 'is_active') or not self.star_camera_widget.is_active:
                return {}
                
            # Get current telemetry from widget
            if hasattr(self.star_camera_widget, 'get_current_telemetry'):
                telemetry = self.star_camera_widget.get_current_telemetry()
                
                # Try to get current image data if available
                image_data = None
                if hasattr(self.star_camera_widget, 'current_image') and self.star_camera_widget.current_image:
                    image = self.star_camera_widget.current_image
                    if image and image.valid and len(image.image_data) > 0:
                        image_data = image.image_data
                        
                if telemetry and telemetry.valid:
                    # Log telemetry data and save image if available
                    star_camera_data = {
                        'ra': telemetry.sc_ra,
                        'dec': telemetry.sc_dec,
                        'field_rotation': telemetry.sc_fr,
                        'image_rotation': telemetry.sc_ir,
                        'azimuth': telemetry.sc_az,
                        'altitude': telemetry.sc_alt,
                        'exposure_time': telemetry.sc_texp,
                        'focus_position': telemetry.sc_curr_focus,
                        'auto_focus_start': telemetry.sc_start_focus,
                        'auto_focus_end': telemetry.sc_end_focus,
                        'focus_step': telemetry.sc_focus_step,
                        'focus_mode': telemetry.sc_focus_mode,
                        'solve_status': telemetry.sc_solve,
                        'save_status': telemetry.sc_save,
                        'image_valid': True
                    }
                    
                    # Save image if available
                    if image_data:
                        image_filename = ''
                        image_path = self.save_image(image_data, star_camera_data)
                        if image_path:
                            image_filename = os.path.basename(image_path)
                        star_camera_data['image_filename'] = image_filename
                    
                    return star_camera_data
            
            # No valid data when widget is inactive
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting star camera data: {e}")
            return {}
            
    def save_image(self, image_data: bytes, telemetry: Dict[str, Any]) -> Optional[str]:
        """Save star camera image with telemetry metadata
        
        Args:
            image_data: Raw image bytes
            telemetry: Dictionary with star camera telemetry
            
        Returns:
            Path to saved image file, or None if failed
        """
        # Save image - quality is already configured in __init__
        return self.image_logger.save_image(image_data, telemetry)
        
            
    def update_data_rate(self) -> None:
        """Update data rate based on widget settings"""
        try:
            # Get update interval from widget
            if hasattr(self.star_camera_widget, 'update_timer'):
                interval_ms = self.star_camera_widget.update_timer.interval()
                rate_hz = 1000.0 / interval_ms if interval_ms > 0 else 1.0
                super().update_data_rate(rate_hz)
        except Exception as e:
            self.logger.error(f"Error updating star camera data rate: {e}")
            

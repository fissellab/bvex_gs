"""
Main Window for BVEX Ground Station
Combines sky chart, GPS display, and spectra display in a professional layout
"""

import sys
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, 
                             QWidget, QMenuBar, QStatusBar, QSplitter,
                             QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction

from src.gui.sky_chart_widget import SkyChartWidget
from src.gui.gps_display_widget import GPSDisplayWidget
from src.gui.spectra_display_widget import SpectraDisplayWidget
from src.gui.star_camera_widget import StarCameraWidget
from src.gui.star_camera_status_widget import StarCameraStatusWidget
from src.data.gps_client import GPSClient
from src.config.settings import GUI, GPS_SERVER, BCP_SPECTROMETER, STAR_CAMERA

class MainWindow(QMainWindow):
    """Main application window for BVEX Ground Station"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.gps_client = GPSClient()
        self.setup_logging()
        self.setup_ui()
        self.setup_timers()
        
        # Connect GPS client
        self.connect_gps()
    
    def setup_logging(self):
        """Setup application logging"""
        import os
        from datetime import datetime
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = os.path.join(log_dir, f'bvex_ground_station_{timestamp}.log')
        
        # Create rotating file handler (max 10MB per file, keep 5 files)
        file_handler = RotatingFileHandler(
            log_filename, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler for warnings and errors only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Reduce verbosity of third-party libraries
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"BVEX Ground Station logging started - Log file: {log_filename}")
        print(f"BVEX Ground Station started - Logs written to: {log_filename}")
        print("Console will only show warnings and errors. All detailed logs are in the file.")
        
        # Clean up old log files (keep last 30 days)
        self._cleanup_old_logs(log_dir)
    
    def _cleanup_old_logs(self, log_dir):
        """Clean up log files older than 30 days"""
        try:
            import os
            import time
            
            current_time = time.time()
            thirty_days_ago = current_time - (30 * 24 * 60 * 60)  # 30 days in seconds
            
            for filename in os.listdir(log_dir):
                if filename.startswith('bvex_ground_station_') and filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = os.path.getmtime(file_path)
                        if file_time < thirty_days_ago:
                            os.remove(file_path)
                            print(f"Cleaned up old log file: {filename}")
        except Exception as e:
            print(f"Warning: Failed to clean up old logs: {e}")
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Set window properties first
        self.setWindowTitle("BVEX Ground Station GUI with Star Camera")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: white; }")
        self.setCentralWidget(central_widget)
        
        # Main layout - three-column layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins to use space efficiently
        main_layout.setSpacing(15)  # Reduced spacing for better space utilization
        
        # Left side - Sky chart and GPS
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15, 0, 5, 0)  # Increased left margin to prevent title cutoff
        left_layout.setSpacing(10)
        
        # Sky chart widget (increased width to prevent title cutoff)
        self.sky_chart_widget = SkyChartWidget()
        self.sky_chart_widget.setMinimumSize(380, 350)  # Increased width to accommodate full title
        self.sky_chart_widget.setMaximumSize(480, 450)  # Increased max width accordingly
        left_layout.addWidget(self.sky_chart_widget)
        
        # GPS widget
        self.gps_widget = GPSDisplayWidget()
        self.gps_widget.setMinimumHeight(300)
        self.gps_widget.setMaximumHeight(400)
        left_layout.addWidget(self.gps_widget)
        
        # Middle - Star Camera section (image and status)
        star_camera_container = QWidget()
        star_camera_layout = QVBoxLayout(star_camera_container)
        star_camera_layout.setContentsMargins(5, 0, 5, 0)  # Minimal margins for efficient space usage
        star_camera_layout.setSpacing(5)
        
        # Star camera image widget (increased height for better aspect ratio)
        self.star_camera_widget = StarCameraWidget()
        self.star_camera_widget.setMinimumSize(520, 350)  # Further increased height to accommodate metadata
        self.star_camera_widget.setMaximumSize(700, 450)  # Further increased max height 
        star_camera_layout.addWidget(self.star_camera_widget, 0, Qt.AlignmentFlag.AlignCenter)  # Center align
        
        # Star camera status widget (new telemetry display)
        self.star_camera_status_widget = StarCameraStatusWidget()
        self.star_camera_status_widget.setMinimumSize(600, 280)  # Slightly reduced to balance with image widget
        self.star_camera_status_widget.setMaximumSize(700, 350)  # Reduced max height for better proportion
        star_camera_layout.addWidget(self.star_camera_status_widget, 0, Qt.AlignmentFlag.AlignCenter)  # Center align
        
        # Right side - Spectra display in a container for top alignment
        spectra_container = QWidget()
        spectra_layout = QVBoxLayout(spectra_container)
        spectra_layout.setContentsMargins(5, 0, 5, 0)
        spectra_layout.setSpacing(0)
        
        self.spectra_widget = SpectraDisplayWidget()
        self.spectra_widget.setMinimumSize(450, 300)  # Reduced height for better proportion
        self.spectra_widget.setMaximumSize(550, 650)  # Set both width and height limits
        
        # Add spectra widget to top of container
        spectra_layout.addWidget(self.spectra_widget, 0, Qt.AlignmentFlag.AlignTop)
        spectra_layout.addStretch()  # Add stretch at bottom to push spectra to top
        
        # Add widgets to main layout with more efficient space usage
        main_layout.addWidget(left_widget, 3)  # Left side gets 3 parts
        main_layout.addWidget(star_camera_container, 5)  # Star camera section gets 5 parts
        main_layout.addWidget(spectra_container, 3)  # Spectra container gets 3 parts - no stretch spaces
        
        # Set window properties - balanced height for all widgets
        self.setMinimumSize(1600, 950)  # Reduced height to match shorter spectrometer
        self.resize(1800, 1000)  # Reduced height for better overall balance
        
        # Setup menu bar
        self.setup_menu_bar()
        
        # Setup status bar
        self.setup_status_bar()
    
    def setup_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Connect/Disconnect GPS
        self.connect_action = QAction('&Connect GPS', self)
        self.connect_action.triggered.connect(self.connect_gps)
        file_menu.addAction(self.connect_action)
        
        self.disconnect_action = QAction('&Disconnect GPS', self)
        self.disconnect_action.triggered.connect(self.disconnect_gps)
        file_menu.addAction(self.disconnect_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Refresh sky chart
        refresh_action = QAction('&Refresh Sky Chart', self)
        refresh_action.triggered.connect(lambda: self.sky_chart_widget.update_chart(0) if self.sky_chart_widget.is_sky_chart_active() else None)
        view_menu.addAction(refresh_action)
        
        # Spectrometer menu
        spectrometer_menu = menubar.addMenu('&Spectrometer')
        
        # Force refresh spectra
        refresh_spectra_action = QAction('&Refresh Spectra', self)
        refresh_spectra_action.triggered.connect(lambda: self.spectra_widget.trigger_fetch() if self.spectra_widget.is_spectrometer_active() else None)
        spectrometer_menu.addAction(refresh_spectra_action)
        
        # Star Camera menu
        star_camera_menu = menubar.addMenu('&Star Camera')
        
        # Force refresh image
        refresh_image_action = QAction('&Refresh Image', self)
        refresh_image_action.triggered.connect(lambda: self.star_camera_widget.request_image() if self.star_camera_widget.is_star_camera_active() else None)
        star_camera_menu.addAction(refresh_image_action)
        
        # Force refresh status
        refresh_status_action = QAction('&Refresh Status', self)
        refresh_status_action.triggered.connect(lambda: self.star_camera_status_widget.update_display() if self.star_camera_status_widget.is_star_camera_status_active() else None)
        star_camera_menu.addAction(refresh_status_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Create application status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("BVEX Ground Station - Initializing...")
        
        # Add data rate status to status bar
        self.data_rate_label = self.create_status_label("Data Rate: 0.0 kB/s")
        self.status_bar.addPermanentWidget(self.data_rate_label)
        
        # Add GPS connection status to status bar
        self.gps_status_label = self.create_status_label("GPS: Disconnected")
        self.status_bar.addPermanentWidget(self.gps_status_label)
        
        # Add spectrometer connection status to status bar
        self.spectrometer_status_label = self.create_status_label("Spectrometer: Disconnected")
        self.status_bar.addPermanentWidget(self.spectrometer_status_label)
        
        # Add star camera connection status to status bar
        self.star_camera_status_label = self.create_status_label("Star Camera: Disconnected")
        self.status_bar.addPermanentWidget(self.star_camera_status_label)
        
        # Add star camera telemetry status to status bar
        self.star_camera_telemetry_status_label = self.create_status_label("SC Telemetry: Disconnected")
        self.status_bar.addPermanentWidget(self.star_camera_telemetry_status_label)
    
    def create_status_label(self, text):
        """Create a status label widget"""
        from PyQt6.QtWidgets import QLabel
        label = QLabel(text)
        label.setStyleSheet("QLabel { border: 1px solid gray; padding: 2px; margin: 2px; }")
        return label
    
    def setup_timers(self):
        """Setup update timers"""
        # GPS data update timer
        self.gps_update_timer = QTimer()
        self.gps_update_timer.timeout.connect(self.update_gps_data)
        self.gps_update_timer.start(GUI['update_interval'])  # Update every second
        
        # Status update timer
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(5000)  # Update every 5 seconds
        
        # Periodic cleanup timer (every hour)
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.periodic_cleanup)
        self.cleanup_timer.start(3600000)  # 1 hour = 3600000 ms
    
    def connect_gps(self):
        """Connect to GPS server"""
        if self.gps_client.start():
            self.status_bar.showMessage("Connecting to GPS server...", 3000)
            self.connect_action.setEnabled(False)
            self.disconnect_action.setEnabled(True)
            self.logger.info("GPS client connection initiated")
        else:
            self.status_bar.showMessage("Failed to connect to GPS server", 5000)
            QMessageBox.warning(
                self, 
                "Connection Error", 
                f"Could not connect to GPS server at {GPS_SERVER['host']}:{GPS_SERVER['port']}"
            )
    
    def disconnect_gps(self):
        """Disconnect from GPS server"""
        self.gps_client.stop()
        self.status_bar.showMessage("GPS disconnected", 3000)
        self.connect_action.setEnabled(True)
        self.disconnect_action.setEnabled(False)
        self.logger.info("GPS client disconnected")
    
    def update_gps_data(self):
        """Update GPS data displays"""
        # Control GPS client based on GPS widget state
        if self.gps_widget.is_gps_active():
            if self.gps_client.is_paused():
                self.gps_client.resume()
        else:
            if not self.gps_client.is_paused():
                self.gps_client.pause()
        
        gps_data = self.gps_client.get_gps_data()
        
        # Update GPS display widget
        self.gps_widget.update_gps_data(gps_data, self.gps_client)
        
        # Update sky chart with GPS data for heading display
        self.sky_chart_widget.set_gps_data(gps_data)
        
        # # Update sky chart location if GPS data is valid
        # # NOTE: This is disabled as per user request to always use the hardcoded
        # # observatory location from the settings file.
        # if gps_data.valid:
        #     self.sky_chart_widget.update_location(gps_data.lat, gps_data.lon, gps_data.alt)
    
    def update_status(self):
        """Update status bar information"""
        # Calculate combined data rate
        total_rate_kbps = 0.0
        
        # Add GPS data rate if active
        if self.gps_widget.is_gps_active():
            gps_rate = self.gps_client.get_data_rate_kbps()
            total_rate_kbps += gps_rate
        
        # Add spectrometer data rate if active
        if self.spectra_widget.is_spectrometer_active():
            spec_rate = self.spectra_widget.get_data_rate_kbps()
            total_rate_kbps += spec_rate
        
        # Add star camera data rate if active
        if self.star_camera_widget.is_star_camera_active():
            star_rate = self.star_camera_widget.get_data_rate_kbps()
            total_rate_kbps += star_rate
        
        # Add star camera telemetry data rate if active
        if self.star_camera_status_widget.is_star_camera_status_active():
            telemetry_rate = self.star_camera_status_widget.oph_client.get_data_rate_kbps()
            total_rate_kbps += telemetry_rate
        
        # Update data rate display
        if total_rate_kbps >= 1000:
            self.data_rate_label.setText(f"Data Rate: {total_rate_kbps/1000:.1f} MB/s")
        else:
            self.data_rate_label.setText(f"Data Rate: {total_rate_kbps:.1f} kB/s")
        
        # Update GPS status
        if not self.gps_widget.is_gps_active():
            gps_status_text = "GPS: Off"
        else:
            gps_data = self.gps_client.get_gps_data()
            if gps_data.valid:
                gps_status_text = f"GPS: Connected ({gps_data.lat:.4f}, {gps_data.lon:.4f})"
            else:
                gps_status_text = "GPS: Disconnected"
        self.gps_status_label.setText(gps_status_text)
        
        # Update spectrometer status
        if not self.spectra_widget.is_spectrometer_active():
            spec_status_text = "Spectrometer: Off"
        elif self.spectra_widget.is_connected():
            spectrum_data = self.spectra_widget.get_spectrum_data()
            if spectrum_data and spectrum_data.valid:
                spec_status_text = f"Spectrometer: {spectrum_data.type} ({spectrum_data.points} pts)"
            else:
                spec_status_text = "Spectrometer: Connected (No Data)"
        else:
            spec_status_text = "Spectrometer: Disconnected"
        self.spectrometer_status_label.setText(spec_status_text)
        
        # Update star camera status
        if not self.star_camera_widget.is_star_camera_active():
            star_status_text = "Star Camera: Off"
        elif self.star_camera_widget.is_connected():
            star_status_text = "Star Camera: Connected"
        else:
            star_status_text = "Star Camera: Disconnected"
        self.star_camera_status_label.setText(star_status_text)
        
        # Update star camera telemetry status
        if not self.star_camera_status_widget.is_star_camera_status_active():
            telemetry_status_text = "SC Telemetry: Off"
        elif self.star_camera_status_widget.is_connected():
            current_data = self.star_camera_status_widget.get_current_data()
            if current_data.valid:
                telemetry_status_text = f"SC Telemetry: Connected (RA: {current_data.sc_ra:.2f}°)"
            else:
                telemetry_status_text = "SC Telemetry: Connected (No Data)"
        else:
            telemetry_status_text = "SC Telemetry: Disconnected"
        self.star_camera_telemetry_status_label.setText(telemetry_status_text)
    
    def periodic_cleanup(self):
        """Perform periodic cleanup to prevent memory buildup during long sessions"""
        try:
            # Trim old data from spectra widget buffers
            if hasattr(self, 'spectra_widget'):
                # Keep only last hour of power data (3600 points at 1Hz)
                max_power_points = 3600
                while len(self.spectra_widget.power_times) > max_power_points:
                    self.spectra_widget.power_times.popleft()
                    self.spectra_widget.power_values.popleft()
                
                # Trim update times buffer
                while len(self.spectra_widget.update_times) > 60:  # Keep last minute
                    self.spectra_widget.update_times.popleft()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            self.logger.info("Periodic cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during periodic cleanup: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>BVEX Ground Station with Spectrometer</h3>
        <p>Balloon-borne VLBI Experiment Ground Station Software</p>
        <p>Real-time sky chart, GPS tracking, and spectrum monitoring for radio astronomy operations</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time sky chart with celestial objects</li>
        <li>GPS coordinate tracking</li>
        <li>Telescope pointing visualization</li>
        <li>Live spectrometer data at 1Hz</li>
        <li>BCP Spectrometer integration (Standard and 120kHz modes)</li>
        </ul>
        <p><b>Servers:</b></p>
        <ul>
        <li>GPS Server: {GPS_SERVER['host']}:{GPS_SERVER['port']}</li>
        <li>BCP Spectrometer: {BCP_SPECTROMETER['host']}:{BCP_SPECTROMETER['port']}</li>
        <li>Star Camera: {STAR_CAMERA['host']}:{STAR_CAMERA['port']}</li>
        </ul>
        """.format(GPS_SERVER=GPS_SERVER, BCP_SPECTROMETER=BCP_SPECTROMETER, STAR_CAMERA=STAR_CAMERA)
        QMessageBox.about(self, "About BVEX Ground Station", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Application shutting down - cleaning up resources...")
        
        # Stop timers
        if hasattr(self, 'gps_update_timer'):
            self.gps_update_timer.stop()
        if hasattr(self, 'status_update_timer'):
            self.status_update_timer.stop()
        if hasattr(self, 'cleanup_timer'):
            self.cleanup_timer.stop()
        
        # Cleanup all components
        try:
            # GPS cleanup
            if hasattr(self, 'gps_client'):
                self.gps_client.cleanup()
            
            # Spectra widget cleanup
            if hasattr(self, 'spectra_widget'):
                self.spectra_widget.cleanup()
            
            # Star camera widget cleanup
            if hasattr(self, 'star_camera_widget'):
                self.star_camera_widget.stop_star_camera()
                if hasattr(self.star_camera_widget, 'worker_thread'):
                    self.star_camera_widget.worker_thread.quit()
                    self.star_camera_widget.worker_thread.wait()
            
            # Star camera status widget cleanup
            if hasattr(self, 'star_camera_status_widget'):
                self.star_camera_status_widget.stop_star_camera_status()
                if hasattr(self.star_camera_status_widget, 'oph_client'):
                    self.star_camera_status_widget.oph_client.cleanup()
            
            # Sky chart cleanup (minimal - just stop animation if running)
            if hasattr(self, 'sky_chart_widget') and self.sky_chart_widget.is_sky_chart_active():
                self.sky_chart_widget.stop_animation()
            
            self.logger.info("Application cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        self.logger.info("BVEX Ground Station shutdown")
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("BVEX Ground Station with Spectrometer")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("BVEX Team")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
 
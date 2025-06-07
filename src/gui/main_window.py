"""
Main Window for BVEX Ground Station
Combines sky chart, GPS display, and spectra display in a professional layout
"""

import sys
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, 
                             QWidget, QMenuBar, QStatusBar, QSplitter,
                             QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction

from src.gui.sky_chart_widget import SkyChartWidget
from src.gui.gps_display_widget import GPSDisplayWidget
from src.gui.spectra_display_widget import SpectraDisplayWidget
from src.data.gps_client import GPSClient
from src.config.settings import GUI, GPS_SERVER, BCP_SPECTROMETER

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
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Set window properties first
        self.setWindowTitle("BVEX Ground Station with Spectrometer")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - horizontal split
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Left side - Sky chart and GPS (rebalanced for better GPS visibility)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Sky chart widget (smaller to make room for GPS)
        self.sky_chart_widget = SkyChartWidget()
        self.sky_chart_widget.setMinimumSize(400, 400)  # Reduced from 500x500
        self.sky_chart_widget.setMaximumSize(500, 500)  # Reduced from 600x600
        left_layout.addWidget(self.sky_chart_widget)
        
        # GPS widget (much larger for better readability)
        self.gps_widget = GPSDisplayWidget()
        self.gps_widget.setMinimumHeight(350)  # Increased significantly from 250
        self.gps_widget.setMaximumHeight(450)  # Increased significantly from 300
        left_layout.addWidget(self.gps_widget)
        
        # Right side - Spectra display (full height)
        self.spectra_widget = SpectraDisplayWidget()
        self.spectra_widget.setMinimumSize(600, 400)  # Minimum size
        
        # Add widgets to main layout with proper proportions
        main_layout.addWidget(left_widget, 1)  # Left side gets 1 part
        main_layout.addWidget(self.spectra_widget, 2)  # Spectra gets 2 parts (larger)
        
        # Set window properties
        self.setMinimumSize(1200, 850)  # Increased height from 700 to accommodate larger GPS
        self.resize(1400, 950)  # Increased height from 800 to give more room
        
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
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Create application status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("BVEX Ground Station - Initializing...")
        
        # Add GPS connection status to status bar
        self.gps_status_label = self.create_status_label("GPS: Disconnected")
        self.status_bar.addPermanentWidget(self.gps_status_label)
        
        # Add spectrometer connection status to status bar
        self.spectrometer_status_label = self.create_status_label("Spectrometer: Disconnected")
        self.status_bar.addPermanentWidget(self.spectrometer_status_label)
    
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
        self.gps_widget.update_gps_data(gps_data)
        
        # Update sky chart with GPS data for heading display
        self.sky_chart_widget.set_gps_data(gps_data)
        
        # # Update sky chart location if GPS data is valid
        # # NOTE: This is disabled as per user request to always use the hardcoded
        # # observatory location from the settings file.
        # if gps_data.valid:
        #     self.sky_chart_widget.update_location(gps_data.lat, gps_data.lon, gps_data.alt)
    
    def update_status(self):
        """Update status bar information"""
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
        </ul>
        """.format(GPS_SERVER=GPS_SERVER, BCP_SPECTROMETER=BCP_SPECTROMETER)
        QMessageBox.about(self, "About BVEX Ground Station", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.gps_client.stop()
        self.spectra_widget.stop_worker()  # Ensure worker thread is stopped
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
 
"""
Main Window for BVEX Ground Station
Combines sky chart and GPS display in a professional layout
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
from src.data.gps_client import GPSClient
from src.config.settings import GUI, GPS_SERVER

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
        """Initialize the user interface"""
        self.setWindowTitle(GUI['window_title'])
        self.setGeometry(100, 100, *GUI['window_size'])
        
        # Create central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sky chart widget (left panel)
        self.sky_chart = SkyChartWidget()
        splitter.addWidget(self.sky_chart)
        
        # GPS display widget (right panel)
        self.gps_display = GPSDisplayWidget()
        splitter.addWidget(self.gps_display)
        
        # Set splitter proportions (sky chart gets most space)
        splitter.setSizes([1000, 350])  # Adjust based on GUI['gps_panel_width']
        splitter.setCollapsible(0, False)  # Don't allow sky chart to collapse
        splitter.setCollapsible(1, False)  # Don't allow GPS panel to collapse
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
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
        refresh_action.triggered.connect(self.sky_chart.update_chart)
        view_menu.addAction(refresh_action)
        
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
        self.gps_status_label = self.status_bar.addPermanentWidget(
            self.create_status_label("GPS: Disconnected")
        )
    
    def create_status_label(self, text):
        """Create a status label widget"""
        from PyQt6.QtWidgets import QLabel
        label = QLabel(text)
        label.setStyleSheet("QLabel { border: 1px solid gray; padding: 2px; }")
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
        gps_data = self.gps_client.get_gps_data()
        
        # Update GPS display widget
        self.gps_display.update_gps_data(gps_data)
        
        # Update sky chart with GPS data for heading display
        self.sky_chart.set_gps_data(gps_data)
        
        # Update sky chart location if GPS data is valid
        if gps_data.valid:
            self.sky_chart.update_location(gps_data.lat, gps_data.lon, gps_data.alt)
    
    def update_status(self):
        """Update status bar information"""
        gps_data = self.gps_client.get_gps_data()
        
        if gps_data.valid:
            status_text = f"GPS: Connected ({gps_data.lat:.4f}, {gps_data.lon:.4f})"
        else:
            status_text = "GPS: Disconnected"
        
        # Update status label
        for widget in self.status_bar.children():
            if hasattr(widget, 'setText') and 'GPS:' in widget.text():
                widget.setText(status_text)
                break
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>BVEX Ground Station</h3>
        <p>Balloon-borne VLBI Experiment Ground Station Software</p>
        <p>Real-time sky chart and GPS tracking for radio astronomy operations</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time sky chart with celestial objects</li>
        <li>GPS coordinate tracking</li>
        <li>Telescope pointing visualization</li>
        </ul>
        """
        QMessageBox.about(self, "About BVEX Ground Station", about_text)
    
    def closeEvent(self, event):
        """Handle application shutdown"""
        self.gps_client.stop()
        self.logger.info("BVEX Ground Station shutdown")
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("BVEX Ground Station")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("BVEX Team")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
 
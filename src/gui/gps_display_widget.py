"""
GPS Display Widget for BVEX Ground Station
Compact display of GPS coordinates and status
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import time

from src.data.gps_client import GPSData, GPSClient
from src.config.settings import GPS_PROCESSING
import logging

class GPSDisplayWidget(QWidget):
    """Compact widget for displaying GPS data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create our own independent GPS client
        self.gps_client = GPSClient()
        self.logger = logging.getLogger(__name__)
        
        self.last_gps_data = GPSData()
        self.is_active = False  # Start OFF by default
        self.setup_ui()
        
        # Setup update timer but don't start it yet
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gps_from_client)
        
        self.logger.info("GPS Widget initialized with independent GPSClient (OFF by default)")
        
    def setup_ui(self):
        """Setup the GPS display interface with clean, professional layout"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("GPS Display: OFF")
        self.control_status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.control_status_label.setStyleSheet("QLabel { color: red; }")
        
        # Toggle button
        self.toggle_button = QPushButton("Turn ON")
        self.toggle_button.setMinimumWidth(100)
        self.toggle_button.clicked.connect(self.toggle_state)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        control_layout.addWidget(self.control_status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(control_layout)
        
        # Create the main container with clean styling
        self.container = QFrame()
        self.container.setFrameStyle(QFrame.Shape.StyledPanel)
        self.container.setStyleSheet("""
            QFrame {
                border: 2px solid #333333;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 5px;
            }
        """)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(3)
        self.container_layout.setContentsMargins(5, 2, 5, 3)
        
        # Initially show static display
        self.setup_static_display()
        
        main_layout.addWidget(self.container)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        self.setMinimumWidth(250)
        self.setMaximumWidth(320)
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_gps_display()
        else:
            self.start_gps_display()
    
    def start_gps_display(self):
        """Start GPS display updates"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("GPS Display: ON")
            self.control_status_label.setStyleSheet("QLabel { color: green; }")
            self.toggle_button.setText("Turn OFF")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            
            # Start our independent GPS client
            if self.gps_client.start():
                self.gps_client.resume()  # Ensure it's not paused
                self.logger.info("GPS client started successfully")
            else:
                self.logger.error("Failed to start GPS client")
            
            # Setup active GPS display
            self.setup_active_display()
            
            # Start update timer
            self.update_timer.start(1000)  # Update every second
    
    def stop_gps_display(self):
        """Stop GPS display updates and show static display"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("GPS Display: OFF")
            self.control_status_label.setStyleSheet("QLabel { color: red; }")
            self.toggle_button.setText("Turn ON")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            
            # Stop update timer
            self.update_timer.stop()
            
            # Stop our independent GPS client
            self.gps_client.stop()
            
            # Show static display
            self.setup_static_display()
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add centered message
        message_label = QLabel("GPS Display - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start GPS updates')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 12))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active GPS display with all data fields"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main data section with Position and Orientation side by side
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
    
    def _create_status_header(self):
        """Create clean GPS connection status header"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.NoFrame)
        header.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 2px;
                margin-bottom: 2px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # GPS Connected text
        self.status_label = QLabel("GPS Connected")
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status indicator dot
        self.status_dot = QLabel("●")
        dot_font = QFont()
        dot_font.setPointSize(16)
        self.status_dot.setFont(dot_font)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addSpacing(8)
        layout.addWidget(self.status_dot)
        layout.addStretch()
        
        # Initialize as disconnected
        self._update_status_display(False)
        
        return header
    
    def _create_data_section(self):
        """Create clean data section with compact 6-field layout inspired by motor widget"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use a clean grid layout with better spacing like motor controller
        layout = QGridLayout(data_frame)
        layout.setSpacing(8)  # Better spacing for cleaner look
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create all field labels with motor widget style
        self.field_labels = {}
        
        # GPS fields arranged in 3 rows, 4 columns (label-value pairs)
        fields = [
            ("lat", "Latitude", "°", 0, 0),
            ("lon", "Longitude", "°", 0, 2),
            ("alt", "Altitude", "m", 1, 0),
            ("head", "Heading", "°", 1, 2),
            ("speed", "Speed", "m/s", 2, 0),
            ("sats", "Satellites", "", 2, 2),
        ]
        
        for field_key, field_name, unit, row, col in fields:
            # Label (clean style like motor controller)
            label = QLabel(f"{field_name}:")
            label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            label.setStyleSheet("color: #495057; border: none; background: transparent;")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Value (clean text style like motor controller, no boxes)
            value_label = QLabel("--")
            if unit:
                value_label.setText(f"-- {unit}")
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #212529; border: none; background: transparent;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setMinimumWidth(60)
            
            # Store reference to value label
            self.field_labels[field_key] = value_label
            
            # Add to grid
            layout.addWidget(label, row, col)
            layout.addWidget(value_label, row, col + 1)
        
        return data_frame
    

    
    def _update_status_display(self, connected: bool):
        """Update the connection status display"""
        if connected:
            self.status_dot.setStyleSheet("color: #28a745;")  # Bootstrap success green
            self.status_label.setText("GPS Connected")
            self.status_label.setStyleSheet("color: #212529;")
        else:
            self.status_dot.setStyleSheet("color: #dc3545;")  # Bootstrap danger red
            self.status_label.setText("GPS Disconnected")
            self.status_label.setStyleSheet("color: #212529;")
    
    def _format_coordinate(self, value: float, is_longitude: bool = False) -> str:
        """Format coordinate values with appropriate precision"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--"
        return f"{value:.3f}"
    
    def _format_altitude(self, value: float) -> str:
        """Format altitude value"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--"
        return f"{value:.1f}"
    
    def _format_heading(self, value: float) -> str:
        """Format heading value"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--"
        return f"{value:.1f} °"
    
    def _format_speed(self, value: float) -> str:
        """Format GPS speed value"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--"
        return f"{value:.2f}"
    
    def _format_satellites(self, value: int) -> str:
        """Format satellite count"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--"
        return f"{value}"
    
    def update_gps_from_client(self):
        """Update GPS data from our own client"""
        if not self.is_active:
            return
        
        # Get data from our independent GPS client
        gps_data = self.gps_client.get_gps_data()
        self.last_gps_data = gps_data
        
        # Update status
        self._update_status_display(gps_data.valid)
        
        # Update all field values using the new compact layout
        if hasattr(self, 'field_labels'):
            self.field_labels['lat'].setText(f"{self._format_coordinate(gps_data.lat)} °")
            self.field_labels['lon'].setText(f"{self._format_coordinate(gps_data.lon)} °")
            self.field_labels['alt'].setText(f"{self._format_altitude(gps_data.alt)} m")
            self.field_labels['head'].setText(f"{self._format_heading(gps_data.head)}")
            self.field_labels['speed'].setText(f"{self._format_speed(gps_data.speed)} m/s")
            self.field_labels['sats'].setText(f"{self._format_satellites(gps_data.sats)}")
        
        # Force widget refresh
        self.update()
    
    def update_gps_data(self, gps_data: GPSData, gps_client=None):
        """Update the display with new GPS data (legacy method for compatibility)"""
        # This method is kept for backwards compatibility but no longer used
        # since the widget now manages its own GPS client
        pass
    
    def get_current_coordinates(self) -> tuple:
        """Return current coordinates for sky chart updates"""
        if self.last_gps_data.valid:
            return (self.last_gps_data.lat, self.last_gps_data.lon, self.last_gps_data.alt)
        return None
    
    def is_gps_active(self) -> bool:
        """Return whether GPS display is currently active"""
        return self.is_active
    
    def cleanup(self):
        """Clean up resources"""
        # Stop our timer
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Stop our independent GPS client
        self.gps_client.stop()
        self.logger.info("GPS client stopped.") 
 
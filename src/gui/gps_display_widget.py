"""
GPS Display Widget for BVEX Ground Station
Compact display of GPS coordinates and status
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import time

from src.data.gps_client import GPSData
from src.config.settings import GPS_PROCESSING

class GPSDisplayWidget(QWidget):
    """Compact widget for displaying GPS data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_gps_data = GPSData()
        self.is_active = False
        self.setup_ui()
        
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
        self.container_layout.setSpacing(2)
        self.container_layout.setContentsMargins(4, 4, 4, 4)
        
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
            
            # Setup active GPS display
            self.setup_active_display()
    
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
        """Create clean data section with Position and Orientation side by side"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use QGridLayout: 1 row, 3 columns (Position | Separator | Orientation)
        main_layout = QGridLayout(data_frame)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Position section (left side) - column 0
        position_section = self._create_position_section()
        main_layout.addWidget(position_section, 0, 0)
        
        # Vertical separator line - column 1
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #dee2e6; }")
        main_layout.addWidget(separator, 0, 1)
        
        # Orientation section (right side) - column 2
        orientation_section = self._create_orientation_section()
        main_layout.addWidget(orientation_section, 0, 2)
        
        return data_frame
    
    def _create_position_section(self):
        """Create clean Position section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section header
        header = QLabel("Position")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: #495057;
                border: none;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 1px;
                margin-bottom: 2px;
            }
        """)
        layout.addWidget(header)
        
        # Latitude
        lat_layout = QVBoxLayout()
        lat_layout.setSpacing(1)
        
        lat_label = QLabel("Latitude:")
        lat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lat_label_font = QFont()
        lat_label_font.setPointSize(10)
        lat_label.setFont(lat_label_font)
        lat_label.setStyleSheet("color: #6c757d;")
        
        self.lat_value = QLabel("--")
        self.lat_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lat_value_font = QFont()
        lat_value_font.setPointSize(12)
        lat_value_font.setBold(True)
        self.lat_value.setFont(lat_value_font)
        self.lat_value.setStyleSheet("color: #212529;")
        
        lat_layout.addWidget(lat_label)
        lat_layout.addWidget(self.lat_value)
        layout.addLayout(lat_layout)
        
        # Longitude
        lon_layout = QVBoxLayout()
        lon_layout.setSpacing(1)
        
        lon_label = QLabel("Longitude:")
        lon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lon_label_font = QFont()
        lon_label_font.setPointSize(10)
        lon_label.setFont(lon_label_font)
        lon_label.setStyleSheet("color: #6c757d;")
        
        self.lon_value = QLabel("--")
        self.lon_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lon_value_font = QFont()
        lon_value_font.setPointSize(12)
        lon_value_font.setBold(True)
        self.lon_value.setFont(lon_value_font)
        self.lon_value.setStyleSheet("color: #212529;")
        
        lon_layout.addWidget(lon_label)
        lon_layout.addWidget(self.lon_value)
        layout.addLayout(lon_layout)
        
        return section
    
    def _create_orientation_section(self):
        """Create clean Orientation section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section header
        header = QLabel("Orientation")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: #495057;
                border: none;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 1px;
                margin-bottom: 2px;
            }
        """)
        layout.addWidget(header)
        
        # Altitude
        alt_layout = QVBoxLayout()
        alt_layout.setSpacing(1)
        
        alt_label = QLabel("Altitude:")
        alt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt_label_font = QFont()
        alt_label_font.setPointSize(10)
        alt_label.setFont(alt_label_font)
        alt_label.setStyleSheet("color: #6c757d;")
        
        self.alt_value = QLabel("-- m")
        self.alt_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt_value_font = QFont()
        alt_value_font.setPointSize(12)
        alt_value_font.setBold(True)
        self.alt_value.setFont(alt_value_font)
        self.alt_value.setStyleSheet("color: #212529;")
        
        alt_layout.addWidget(alt_label)
        alt_layout.addWidget(self.alt_value)
        layout.addLayout(alt_layout)
        
        # Heading
        head_layout = QVBoxLayout()
        head_layout.setSpacing(1)
        
        head_label = QLabel("Heading:")
        head_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head_label_font = QFont()
        head_label_font.setPointSize(10)
        head_label.setFont(head_label_font)
        head_label.setStyleSheet("color: #6c757d;")
        
        self.head_value = QLabel("--")
        self.head_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head_value_font = QFont()
        head_value_font.setPointSize(12)
        head_value_font.setBold(True)
        self.head_value.setFont(head_value_font)
        self.head_value.setStyleSheet("color: #212529;")
        
        head_layout.addWidget(head_label)
        head_layout.addWidget(self.head_value)
        layout.addLayout(head_layout)
        
        return section
    
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
        """Format coordinate values with appropriate precision - simplified for clean display"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--"
        
        # Simplified format without direction indicator for cleaner look
        return f"{abs(value):.3f}"
    
    def _format_altitude(self, value: float) -> str:
        """Format altitude value"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "-- m"
        return f"{value:.2f} m"
    
    def _format_heading(self, value: float) -> str:
        """Format heading value with cardinal direction"""
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--"
        
        # Convert to cardinal directions
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = int((value + 11.25) / 22.5) % 16
        cardinal = directions[index]
        
        return f"{value:.2f} ({cardinal})"
    
    def update_gps_data(self, gps_data: GPSData, gps_client=None):
        """Update the display with new GPS data"""
        self.last_gps_data = gps_data
        
        # Only update display if GPS display is active
        if not self.is_active:
            return
        
        # Update status
        self._update_status_display(gps_data.valid)
        
        # Update coordinate values
        self.lat_value.setText(self._format_coordinate(gps_data.lat, False))
        self.lon_value.setText(self._format_coordinate(gps_data.lon, True))
        self.alt_value.setText(self._format_altitude(gps_data.alt))
        self.head_value.setText(self._format_heading(gps_data.head))
        
        # Force widget refresh
        self.update()
    
    def get_current_coordinates(self) -> tuple:
        """Return current coordinates for sky chart updates"""
        if self.last_gps_data.valid:
            return (self.last_gps_data.lat, self.last_gps_data.lon, self.last_gps_data.alt)
        return None
    
    def is_gps_active(self) -> bool:
        """Return whether GPS display is currently active"""
        return self.is_active 
 
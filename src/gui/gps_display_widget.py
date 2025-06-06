"""
GPS Display Widget for BVEX Ground Station
Compact display of GPS coordinates and status
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame)
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
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GPS display interface with clean, professional layout"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create the main container with clean styling
        container = QFrame()
        container.setFrameStyle(QFrame.Shape.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                border: 2px solid #333333;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 5px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(10, 10, 10, 10)
        
        # Status header
        self.status_header = self._create_status_header()
        container_layout.addWidget(self.status_header)
        
        # Main data section with Position and Orientation side by side
        data_section = self._create_data_section()
        container_layout.addWidget(data_section)
        
        main_layout.addWidget(container)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        self.setMinimumWidth(320)
        self.setMaximumWidth(400)
    
    def _create_status_header(self):
        """Create clean GPS connection status header"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.NoFrame)
        header.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 8px;
                margin-bottom: 8px;
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
        
        # Main horizontal layout for Position | Orientation
        main_layout = QHBoxLayout(data_frame)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Position section (left side)
        position_section = self._create_position_section()
        main_layout.addWidget(position_section)
        
        # Vertical separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #dee2e6; }")
        main_layout.addWidget(separator)
        
        # Orientation section (right side)
        orientation_section = self._create_orientation_section()
        main_layout.addWidget(orientation_section)
        
        return data_frame
    
    def _create_position_section(self):
        """Create clean Position section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
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
                padding-bottom: 4px;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(header)
        
        # Latitude
        lat_layout = QVBoxLayout()
        lat_layout.setSpacing(2)
        
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
        lon_layout.setSpacing(2)
        
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
        layout.setSpacing(8)
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
                padding-bottom: 4px;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(header)
        
        # Altitude
        alt_layout = QVBoxLayout()
        alt_layout.setSpacing(2)
        
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
        head_layout.setSpacing(2)
        
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
    
    def update_gps_data(self, gps_data: GPSData):
        """Update the display with new GPS data"""
        self.last_gps_data = gps_data
        
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
 
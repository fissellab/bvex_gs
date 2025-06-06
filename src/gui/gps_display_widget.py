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
        """Setup the GPS display interface"""
        layout = QVBoxLayout()
        layout.setSpacing(8)  # Increased spacing for better visibility
        layout.setContentsMargins(5, 5, 5, 5)  # Add some margins
        
        # Title
        title_label = QLabel("GPS DATA")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status indicator
        self.status_frame = self._create_status_indicator()
        layout.addWidget(self.status_frame)
        
        # GPS coordinates group
        coords_group = self._create_coordinates_group()
        layout.addWidget(coords_group)
        
        # Altitude and heading group
        alt_head_group = self._create_altitude_heading_group()
        layout.addWidget(alt_head_group)
        
        # Timestamp
        self.timestamp_label = QLabel("Last Update: --")
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timestamp_label.setStyleSheet("color: gray; font-size: 9px;")
        layout.addWidget(self.timestamp_label)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        self.setLayout(layout)
        self.setMaximumWidth(350)
        self.setMinimumWidth(300)
    
    def _create_status_indicator(self):
        """Create GPS connection status indicator"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        layout = QHBoxLayout()
        
        self.status_dot = QLabel("●")
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("DISCONNECTED")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_label)
        frame.setLayout(layout)
        
        self._update_status_display(False)
        return frame
    
    def _create_coordinates_group(self):
        """Create latitude/longitude display group"""
        group = QGroupBox("Position")
        group.setMinimumHeight(80)  # Set minimum height for proper display
        layout = QGridLayout()
        layout.setSpacing(8)  # Increased spacing between elements
        layout.setContentsMargins(15, 15, 15, 15)  # Increased margins for better padding
        layout.setRowMinimumHeight(0, 25)  # Set minimum row height
        layout.setRowMinimumHeight(1, 25)  # Set minimum row height
        
        # Latitude
        lat_label = QLabel("Latitude:")
        lat_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lat_value = QLabel("--°")
        self.lat_value.setStyleSheet("font-family: monospace; font-weight: bold; font-size: 11px;")
        
        # Longitude
        lon_label = QLabel("Longitude:")
        lon_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lon_value = QLabel("--°")
        self.lon_value.setStyleSheet("font-family: monospace; font-weight: bold; font-size: 11px;")
        
        layout.addWidget(lat_label, 0, 0)
        layout.addWidget(self.lat_value, 0, 1)
        layout.addWidget(lon_label, 1, 0)
        layout.addWidget(self.lon_value, 1, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_altitude_heading_group(self):
        """Create altitude and heading display group"""
        group = QGroupBox("Orientation")
        group.setMinimumHeight(80)  # Set minimum height for proper display
        layout = QGridLayout()
        layout.setSpacing(8)  # Increased spacing between elements
        layout.setContentsMargins(15, 15, 15, 15)  # Increased margins for better padding
        layout.setRowMinimumHeight(0, 25)  # Set minimum row height
        layout.setRowMinimumHeight(1, 25)  # Set minimum row height
        
        # Altitude
        alt_label = QLabel("Altitude:")
        alt_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.alt_value = QLabel("-- m")
        self.alt_value.setStyleSheet("font-family: monospace; font-weight: bold; font-size: 11px;")
        
        # Heading
        head_label = QLabel("Heading:")
        head_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.head_value = QLabel("--°")
        self.head_value.setStyleSheet("font-family: monospace; font-weight: bold; font-size: 11px;")
        
        layout.addWidget(alt_label, 0, 0)
        layout.addWidget(self.alt_value, 0, 1)
        layout.addWidget(head_label, 1, 0)
        layout.addWidget(self.head_value, 1, 1)
        
        group.setLayout(layout)
        return group
    
    def _update_status_display(self, connected: bool):
        """Update the connection status display"""
        if connected:
            self.status_dot.setStyleSheet("color: green; font-size: 16px;")
            self.status_label.setText("CONNECTED")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_dot.setStyleSheet("color: red; font-size: 16px;")
            self.status_label.setText("DISCONNECTED")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def _format_coordinate(self, value: float, is_longitude: bool = False) -> str:
        """Format coordinate values with appropriate precision"""
        # For GPS coordinates, 0.0 could be a valid coordinate (Gulf of Guinea)
        # So we need to check if the GPS data itself is valid rather than the coordinate value
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--°"
        
        direction = ""
        if is_longitude:
            direction = "E" if value >= 0 else "W"
        else:
            direction = "N" if value >= 0 else "S"
        
        return f"{abs(value):.6f}° {direction}"
    
    def _format_altitude(self, value: float) -> str:
        """Format altitude value"""
        # Check if GPS data is valid rather than altitude value
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "-- m"
        return f"{value:.1f} m"
    
    def _format_heading(self, value: float) -> str:
        """Format heading value with cardinal direction"""
        # Check if GPS data is valid rather than heading value
        if not hasattr(self, 'last_gps_data') or not self.last_gps_data.valid:
            return "--°"
        
        # Convert to cardinal directions
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = int((value + 11.25) / 22.5) % 16
        cardinal = directions[index]
        
        return f"{value:.1f}° ({cardinal})"
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display"""
        if timestamp is None:
            return "Last Update: --"
        
        time_diff = time.time() - timestamp
        if time_diff < 60:
            return f"Last Update: {int(time_diff)}s ago"
        elif time_diff < 3600:
            return f"Last Update: {int(time_diff/60)}m ago"
        else:
            return f"Last Update: {int(time_diff/3600)}h ago"
    
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
        
        # Update timestamp
        self.timestamp_label.setText(self._format_timestamp(gps_data.timestamp))
        
        # Force widget refresh
        self.update()
    
    def get_current_coordinates(self) -> tuple:
        """Return current coordinates for sky chart updates"""
        if self.last_gps_data.valid:
            return (self.last_gps_data.lat, self.last_gps_data.lon, self.last_gps_data.alt)
        return None 
 
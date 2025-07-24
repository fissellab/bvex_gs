"""
Heater System Widget for BVEX Ground Station
Clean display and control of heater relay states and system status
"""

import sys
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QApplication, QPushButton)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from datetime import datetime

from src.data.heater_client import HeaterClient, HeaterData
from src.config.settings import HEATER_SERVER


class StatusIndicator(QLabel):
    """Custom widget to display colored indicator for heater status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_on = None  # None = Unknown, True = ON, False = OFF
        self.setFixedSize(12, 12)
    
    def set_status(self, is_on):
        """Set the status and update the display"""
        self.is_on = is_on
        self.update()
    
    def paintEvent(self, event):
        """Paint the colored indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Choose color based on status
        if self.is_on is None:
            color = QColor(108, 117, 125)  # Gray for unknown
        elif self.is_on:
            color = QColor(40, 167, 69)  # Green for ON
        else:
            color = QColor(220, 53, 69)  # Red for OFF
        
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawEllipse(1, 1, 10, 10)


class HeaterWidget(QWidget):
    """Clean widget for displaying and controlling heater system"""
    
    def __init__(self, parent=None, server_ip=None, server_port=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize heater client
        self.heater_client = HeaterClient(
            host=server_ip or HEATER_SERVER['host'],
            port=server_port or HEATER_SERVER['port']
        )
        
        # Control state - start OFF by default to save resources
        self.is_active = False
        
        # Setup the UI
        self.setup_ui()
        
        self.logger.info("Heater Widget initialized (OFF by default)")
    
    def setup_ui(self):
        """Initialize the clean user interface matching other widget styles"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Heater System: OFF")
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
        
        # Create the main container with clean styling like other widgets
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
        
        # Set proper size - similar to other housekeeping widgets
        self.setMinimumSize(650, 280)
        self.setMaximumSize(750, 320)
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_heater_system()
        else:
            self.start_heater_system()
    
    def start_heater_system(self):
        """Start heater monitoring and control"""
        self.is_active = True
        self.control_status_label.setText("Heater System: ON")
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
        
        # Setup active display
        self.setup_active_display()
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        self.logger.info("Heater system widget activated")
    
    def stop_heater_system(self):
        """Stop heater monitoring"""
        self.is_active = False
        self.control_status_label.setText("Heater System: OFF")
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
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Setup static display
        self.setup_static_display()
        
        self.logger.info("Heater system widget deactivated")
    
    def setup_static_display(self):
        """Setup static display when widget is OFF"""
        # Clear existing layout
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().setParent(None)
        
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Static info section
        info_section = self._create_static_info_section()
        self.container_layout.addWidget(info_section)
    
    def setup_active_display(self):
        """Setup active heater control display with toggle buttons"""
        # Clear existing layout
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().setParent(None)
        
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main data section
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
    
    def _create_status_header(self):
        """Create the status header section"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.NoFrame)
        header.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Heater System Control")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("QLabel { color: #495057; border: none; }")
        
        # Connection status
        self.connection_status_label = QLabel("Disconnected")
        self.connection_status_label.setFont(QFont("Arial", 10))
        self.connection_status_label.setStyleSheet("QLabel { color: #dc3545; border: none; }")
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self.connection_status_label)
        
        return header
    
    def _create_static_info_section(self):
        """Create static information section when OFF"""
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.NoFrame)
        info_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QVBoxLayout(info_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Info text
        info_text = QLabel("""
Heater System Control

- Lock Pin Heater (Temp-controlled)
- Star Camera Heater (Temp-controlled)  
- PV Panel Heater (Manual-only)
- Motor Heater (Temp-controlled)
- Ethernet Switch Heater (Temp-controlled)

Total Current Limit: 3A
Temperature Range: 28-30°C (auto)
        """.strip())
        info_text.setFont(QFont("Arial", 10))
        info_text.setStyleSheet("QLabel { color: #6c757d; border: none; }")
        info_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        layout.addWidget(info_text)
        layout.addStretch()
        
        return info_frame
    
    def _create_data_section(self):
        """Create the main data display section with heater controls"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use a grid layout for organized display
        layout = QGridLayout(data_frame)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create field labels and button storage
        self.status_indicators = {}
        self.toggle_buttons = {}
        
        # Heater controls - organized by type
        row = 0
        
        # Headers
        headers = ["Heater", "Status", "Control", "Type"]
        for col, header in enumerate(headers):
            header_label = QLabel(f"{header}:")
            header_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            header_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter if col > 0 else Qt.AlignmentFlag.AlignLeft)
            header_label.setMinimumHeight(26)
            layout.addWidget(header_label, row, col)
        row += 1
        
        # Heater definitions
        heaters = [
            ("Lock Pin", "lockpin", "Temp-Ctrl"),
            ("Star Camera", "starcamera", "Temp-Ctrl"),
            ("PV Panel", "pv",  "Manual"),
            ("Motor", "motor", "Temp-Ctrl"),
            ("Ethernet", "ethernet", "Temp-Ctrl" )
        ]
        
        for heater_name, heater_key, heater_type in heaters:
            # Heater name
            name_label = QLabel(f"{heater_name}:")
            name_label.setFont(QFont("Arial", 10))
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            layout.addWidget(name_label, row, 0)
            
            # Status indicator
            indicator = StatusIndicator()
            layout.addWidget(indicator, row, 1, Qt.AlignmentFlag.AlignCenter)
            self.status_indicators[heater_key] = indicator
            
            # Toggle button
            toggle_btn = QPushButton("Toggle")
            toggle_btn.setMinimumWidth(70)
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            toggle_btn.clicked.connect(lambda checked, key=heater_key: self.toggle_heater(key))
            layout.addWidget(toggle_btn, row, 2, Qt.AlignmentFlag.AlignCenter)
            self.toggle_buttons[heater_key] = toggle_btn
            
            # Type label
            type_label = QLabel(heater_type)
            type_label.setFont(QFont("Arial", 9))
            type_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            type_label.setStyleSheet("QLabel { color: #868e96; border: none; background: transparent; }")
            layout.addWidget(type_label, row, 3)
            
            row += 1
        
        # System status row
        layout.addWidget(QLabel(""), row, 0)  # Spacer
        row += 1
        
        # System status
        status_label = QLabel("System Status:")
        status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
        status_label.setMinimumHeight(26)
        layout.addWidget(status_label, row, 0)
        
        self.system_status_label = QLabel("Unknown")
        self.system_status_label.setFont(QFont("Arial", 10))
        self.system_status_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        layout.addWidget(self.system_status_label, row, 1, 1, 3)
        
        return data_frame
    
    def toggle_heater(self, heater_key):
        """Toggle a specific heater"""
        try:
            # Get the appropriate toggle method
            toggle_methods = {
                'lockpin': self.heater_client.toggle_lockpin,
                'starcamera': self.heater_client.toggle_starcamera,
                'pv': self.heater_client.toggle_pv,
                'motor': self.heater_client.toggle_motor,
                'ethernet': self.heater_client.toggle_ethernet
            }
            
            if heater_key in toggle_methods:
                success = toggle_methods[heater_key]()
                if success:
                    self.logger.info(f"Successfully toggled {heater_key} heater")
                    # Update display immediately
                    self.update_display()
                else:
                    self.logger.warning(f"Failed to toggle {heater_key} heater")
                    
        except Exception as e:
            self.logger.error(f"Error toggling {heater_key} heater: {e}")
    
    def update_display(self):
        """Update the display with current data"""
        if not self.is_active:
            return
        
        try:
            # Get current data
            data = self.heater_client.get_current_data()
            
            # Update connection status
            if self.heater_client.is_connected():
                self.connection_status_label.setText("Connected")
                self.connection_status_label.setStyleSheet("QLabel { color: #28a745; border: none; }")
            else:
                self.connection_status_label.setText("Disconnected")
                self.connection_status_label.setStyleSheet("QLabel { color: #dc3545; border: none; }")
            
            # Update system status
            if data.system_online:
                if data.last_command_success:
                    self.system_status_label.setText("Online - Last command: Success")
                    self.system_status_label.setStyleSheet("QLabel { color: #28a745; border: none; }")
                else:
                    self.system_status_label.setText(f"Online - Error: {data.last_error}")
                    self.system_status_label.setStyleSheet("QLabel { color: #ffc107; border: none; }")
            else:
                self.system_status_label.setText(f"Offline - {data.last_error}")
                self.system_status_label.setStyleSheet("QLabel { color: #dc3545; border: none; }")
            
            # Update status indicators (we don't have actual state feedback, so show unknown)
            for key, indicator in self.status_indicators.items():
                # Since the heater server only accepts toggle commands and doesn't provide status,
                # we show unknown status (gray indicators)
                indicator.set_status(None)
                
        except Exception as e:
            self.logger.error(f"Error updating heater display: {e}")
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        if hasattr(self, 'heater_client'):
            self.heater_client.cleanup()
        
        self.logger.info("Heater widget cleaned up")


# Test the widget standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = HeaterWidget()
    widget.show()
    
    sys.exit(app.exec()) 

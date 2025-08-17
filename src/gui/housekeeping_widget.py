"""
BCP Housekeeping Widget for BVEX Ground Station
Clean display of housekeeping sensor data including temperatures and pressure
"""

import sys
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QApplication, QPushButton)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from datetime import datetime

from src.data.housekeeping_client import HousekeepingClient, HousekeepingData


class StatusIndicator(QLabel):
    """Custom widget to display colored indicator for system status"""
    
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


class HousekeepingWidget(QWidget):
    """Clean widget for displaying BCP housekeeping sensor data"""
    
    def __init__(self, parent=None, server_ip="127.0.0.1", server_port=8002):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize housekeeping client
        self.housekeeping_client = HousekeepingClient(server_ip=server_ip, server_port=server_port)
        
        # Control state - start OFF by default to save resources
        self.is_active = False
        
        # Setup the UI
        self.setup_ui()
        
        self.logger.info("Housekeeping Widget initialized (OFF by default)")
    
    def setup_ui(self):
        """Initialize the clean user interface matching GPS/VLBI widget style"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("BCP Housekeeping: OFF")
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
        
        self.setLayout(main_layout)
        self.setMinimumWidth(320)  # More compact for 4-column layout
        self.setMaximumWidth(400)  # More compact
        self.setMinimumHeight(280)  # More compact
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add centered message
        message_label = QLabel("BCP Housekeeping - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start housekeeping monitoring')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 12))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active housekeeping display with clean GPS-style layout"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Status header (clean style like GPS)
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main data section
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
    
    def _create_status_header(self):
        """Create clean housekeeping connection status header like GPS widget"""
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
        
        # BCP Housekeeping Connected text
        self.status_label = QLabel("BCP Housekeeping Connected")
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # System status indicators (powered and running)
        powered_label = QLabel("Powered:")
        powered_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        powered_label.setStyleSheet("color: #495057; border: none; background: transparent;")
        self.powered_indicator = StatusIndicator()
        
        running_label = QLabel("Running:")
        running_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        running_label.setStyleSheet("color: #495057; border: none; background: transparent;")
        self.running_indicator = StatusIndicator()
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(powered_label)
        layout.addWidget(self.powered_indicator)
        layout.addSpacing(10)
        layout.addWidget(running_label)
        layout.addWidget(self.running_indicator)
        
        # Initialize as disconnected
        self._update_status_display(False)
        
        return header
    
    def _create_data_section(self):
        """Create clean data section with temperature and pressure fields like GPS widget"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use a clean grid layout like GPS widget
        layout = QGridLayout(data_frame)
        layout.setSpacing(6)  # Clean spacing
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Store all field labels for updates
        self.field_labels = {}
        
        # Temperature sensors arranged in compact grid (label:value pairs)
        temp_sensors = [
            ("OCXO", "hk_ocxo_temp", "°C", 0, 0),
            ("IF Amp", "hk_ifamp_temp", "°C", 0, 2),
            ("LO", "hk_lo_temp", "°C", 0, 4),
            ("TEC", "hk_tec_temp", "°C", 1, 0),
            ("Backend", "hk_backend_chassis_temp", "°C", 1, 2),
            ("NIC", "hk_nic_temp", "°C", 1, 4),
            ("RFSoC Chassis", "hk_rfsoc_chassis_temp", "°C", 2, 0),
            ("RFSoC Chip", "hk_rfsoc_chip_temp", "°C", 2, 2),
            ("LNA1", "hk_lna1_temp", "°C", 2, 4),
            ("LNA2", "hk_lna2_temp", "°C", 3, 0),
        ]
        
        # Add temperature fields
        for display_name, field_key, unit, row, col in temp_sensors:
            # Label (clean style like GPS)
            label = QLabel(f"{display_name}:")
            label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            label.setStyleSheet("color: #495057; border: none; background: transparent;")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Value (clean text style like GPS, no boxes)
            value_label = QLabel(f"-- {unit}")
            value_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setMinimumWidth(50)
            
            # Store reference to value label
            self.field_labels[field_key] = value_label
            
            # Add to grid
            layout.addWidget(label, row, col)
            layout.addWidget(value_label, row, col + 1)
        
        # Add pressure field (special row)
        pressure_label = QLabel("PV Pressure:")
        pressure_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        pressure_label.setStyleSheet("color: #495057; border: none; background: transparent;")
        pressure_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.pressure_value_label = QLabel("-- bar")
        self.pressure_value_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.pressure_value_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        self.pressure_value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(pressure_label, 3, 2)
        layout.addWidget(self.pressure_value_label, 3, 3)
        
        # Add timestamp at bottom
        self.timestamp_label = QLabel("Last Update: Never")
        self.timestamp_label.setFont(QFont("Arial", 7))
        self.timestamp_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timestamp_label, 4, 0, 1, 6)
        
        return data_frame
    
    def _update_status_display(self, connected):
        """Update the status header display"""
        if connected:
            self.status_label.setText("BCP Housekeeping Connected")
            self.status_label.setStyleSheet("color: #28a745; border: none; background: transparent;")
        else:
            self.status_label.setText("BCP Housekeeping Disconnected")
            self.status_label.setStyleSheet("color: #dc3545; border: none; background: transparent;")
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_housekeeping()
        else:
            self.start_housekeeping()
    
    def start_housekeeping(self):
        """Start housekeeping monitoring"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("BCP Housekeeping: ON")
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
            
            self.logger.info("Housekeeping monitoring started")
    
    def stop_housekeeping(self):
        """Stop housekeeping monitoring"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("BCP Housekeeping: OFF")
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
            
            # Show static display
            self.setup_static_display()
            
            self.logger.info("Housekeeping monitoring stopped")
    
    def update_display(self):
        """Update the housekeeping display with latest data"""
        if not self.is_active:
            return
        
        # Update data from client
        success = self.housekeeping_client.update_data()
        current_data = self.housekeeping_client.current_data
        
        if success and current_data.valid:
            # Update connection status
            self._update_status_display(True)
            
            # Update system status indicators
            self.powered_indicator.set_status(current_data.hk_powered == 1)
            self.running_indicator.set_status(current_data.hk_running == 1)
            
            # Update temperature readings with color coding (clean GPS-style)
            for sensor_key, label in self.field_labels.items():
                temp_value = getattr(current_data, sensor_key, -999.0)
                
                if temp_value == -999.0:
                    label.setText("ERROR")
                    label.setStyleSheet("color: #6c757d; border: none; background: transparent;")  # Gray for error
                else:
                    label.setText(f"{temp_value:.1f}°C")
                    # Apply color coding based on temperature status
                    status = self.housekeeping_client.get_temperature_status(temp_value)
                    if status == "normal":
                        label.setStyleSheet("color: #28a745; border: none; background: transparent; font-weight: bold;")  # Green
                    elif status == "warning":
                        label.setStyleSheet("color: #ffc107; border: none; background: transparent; font-weight: bold;")  # Yellow
                    elif status == "critical":
                        label.setStyleSheet("color: #dc3545; border: none; background: transparent; font-weight: bold;")  # Red
                    else:  # error
                        label.setStyleSheet("color: #6c757d; border: none; background: transparent;")  # Gray
            
            # Update pressure reading
            pressure_value = current_data.hk_pv_pressure_bar
            if pressure_value == -999.0:
                self.pressure_value_label.setText("INVALID")
                self.pressure_value_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
            else:
                self.pressure_value_label.setText(f"{pressure_value:.3f} bar")
                # Apply color coding based on pressure status
                status = self.housekeeping_client.get_pressure_status(pressure_value)
                if status == "normal":
                    self.pressure_value_label.setStyleSheet("color: #28a745; border: none; background: transparent; font-weight: bold;")
                else:
                    self.pressure_value_label.setStyleSheet("color: #ffc107; border: none; background: transparent; font-weight: bold;")
            
            # Update timestamp
            timestamp_str = datetime.fromtimestamp(current_data.timestamp).strftime("%H:%M:%S")
            self.timestamp_label.setText(f"Last Update: {timestamp_str}")
            self.timestamp_label.setStyleSheet("color: #28a745; border: none; background: transparent;")
        else:
            # Connection failed - show disconnected state
            self._update_status_display(False)
            if hasattr(self, 'timestamp_label'):
                self.timestamp_label.setText("Last Update: Connection Failed")
                self.timestamp_label.setStyleSheet("color: #dc3545; border: none; background: transparent;")
    
    def is_housekeeping_active(self) -> bool:
        """Check if housekeeping monitoring is active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Check if housekeeping client is connected"""
        return self.housekeeping_client.is_connected()
    
    def get_current_data(self) -> HousekeepingData:
        """Get current housekeeping data"""
        return self.housekeeping_client.current_data
    
    def get_connection_stats(self):
        """Get connection statistics"""
        return self.housekeeping_client.get_connection_stats()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.is_active:
            self.stop_housekeeping()
        self.housekeeping_client.cleanup()
        self.logger.info("Housekeeping widget cleanup completed")


if __name__ == "__main__":
    # Test the widget standalone
    app = QApplication(sys.argv)
    widget = HousekeepingWidget()
    widget.show()
    sys.exit(app.exec())

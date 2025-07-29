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
from src.config.settings import HEATER_SERVER, HEATER_TELEMETRY


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
        
        # Info text - Updated to match guide specifications
        info_text = QLabel("""
Heater System Control (HEATER_CLIENT_GUIDE.md)

Individual Heater Components:
- Star Camera Heater (28-30°C auto)
- Motor Heater (25-27°C auto)  
- Ethernet Switch Heater (20-22°C auto)
- Lock Pin Heater (15-17°C auto)
- Spare/General Heater (Manual only)

System Limits:
• Total Current Limit: 3A
• Priority-based control (coldest first)
• Real-time telemetry monitoring
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
        self.temp_labels = {}
        self.current_labels = {}
        
        # Headers
        headers = ["Component", "Status", "Temp (°C)", "Current (A)", "Control"]
        for col, header in enumerate(headers):
            header_label = QLabel(f"{header}:")
            header_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            header_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter if col > 0 else Qt.AlignmentFlag.AlignLeft)
            header_label.setMinimumHeight(26)
            layout.addWidget(header_label, 0, col)
        
        # Heater definitions - CORRECTED according to guide
        # Command -> Component mapping from guide
        heaters = [
            ("Star Camera", "starcam", "Auto (28-30°C)", "toggle_starcam_auto"),
            ("Motor", "motor", "Auto (25-27°C)", "toggle_motor_auto"),
            ("Ethernet Switch", "ethernet", "Auto (20-22°C)", "toggle_ethernet_auto"),
            ("Lock Pin", "lockpin", "Auto (15-17°C)", "toggle_lockpin_auto"),
            ("Spare/General", "spare", "Manual Only", "toggle_spare_heater")
        ]
        
        row = 1
        for heater_name, heater_key, heater_type, method_name in heaters:
            # Component name
            name_label = QLabel(f"{heater_name}:")
            name_label.setFont(QFont("Arial", 10))
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            layout.addWidget(name_label, row, 0)
            
            # Status indicator
            indicator = StatusIndicator()
            layout.addWidget(indicator, row, 1, Qt.AlignmentFlag.AlignCenter)
            self.status_indicators[heater_key] = indicator
            
            # Temperature display
            temp_label = QLabel("--")
            temp_label.setFont(QFont("Arial", 9))
            temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            temp_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            layout.addWidget(temp_label, row, 2)
            self.temp_labels[heater_key] = temp_label
            
            # Current display
            current_label = QLabel("--")
            current_label.setFont(QFont("Arial", 9))
            current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            current_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            layout.addWidget(current_label, row, 3)
            self.current_labels[heater_key] = current_label
            
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
            toggle_btn.clicked.connect(lambda checked, method=method_name: self.toggle_heater_new(method))
            layout.addWidget(toggle_btn, row, 4, Qt.AlignmentFlag.AlignCenter)
            self.toggle_buttons[heater_key] = toggle_btn
            
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
        layout.addWidget(self.system_status_label, row, 1, 1, 2)
        
        # Total current display
        self.total_current_label = QLabel("Total: -- A")
        self.total_current_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.total_current_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
        layout.addWidget(self.total_current_label, row, 3, 1, 2)
        
        return data_frame
    
    def toggle_heater_new(self, method_name):
        """Toggle a specific heater using the correct method"""
        try:
            # Get the method from the heater client
            if hasattr(self.heater_client, method_name):
                method = getattr(self.heater_client, method_name)
                success = method()
                if success:
                    self.logger.info(f"Successfully executed {method_name}")
                    # Update display immediately
                    self.update_display()
                else:
                    self.logger.warning(f"Failed to execute {method_name}")
            else:
                self.logger.error(f"Method {method_name} not found in heater client")
                    
        except Exception as e:
            self.logger.error(f"Error executing {method_name}: {e}")
    
    def toggle_heater(self, heater_key):
        """Legacy toggle method - deprecated"""
        self.logger.warning(f"Using legacy toggle_heater method for {heater_key} - this may have incorrect mappings!")
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
            # Get current data (which will update telemetry)
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
                if data.system_running:
                    self.system_status_label.setText("Online & Running")
                    self.system_status_label.setStyleSheet("QLabel { color: #28a745; border: none; }")
                else:
                    self.system_status_label.setText("Online but Stopped")
                    self.system_status_label.setStyleSheet("QLabel { color: #ffc107; border: none; }")
            else:
                self.system_status_label.setText(f"Offline - {data.last_error}")
                self.system_status_label.setStyleSheet("QLabel { color: #dc3545; border: none; }")
            
            # Update total current
            if data.total_current > 0:
                current_color = "#dc3545" if data.total_current > 2.5 else "#28a745"  # Red if near 3A limit
                self.total_current_label.setText(f"Total: {data.total_current:.2f} A")
                self.total_current_label.setStyleSheet(f"QLabel {{ color: {current_color}; border: none; }}")
            else:
                self.total_current_label.setText("Total: -- A")
                self.total_current_label.setStyleSheet("QLabel { color: #6c757d; border: none; }")
            
            # Update individual heater status indicators and telemetry
            heater_data_map = {
                'starcam': (data.starcam_state, data.starcam_temp, data.starcam_current),
                'motor': (data.motor_state, data.motor_temp, data.motor_current),
                'ethernet': (data.ethernet_state, data.ethernet_temp, data.ethernet_current),
                'lockpin': (data.lockpin_state, data.lockpin_temp, data.lockpin_current),
                'spare': (data.spare_state, data.spare_temp, data.spare_current)
            }
            
            for key, (state, temp, current) in heater_data_map.items():
                # Update status indicator
                if key in self.status_indicators:
                    self.status_indicators[key].set_status(state)
                
                # Update temperature display
                if key in self.temp_labels:
                    if temp > 0:
                        self.temp_labels[key].setText(f"{temp:.1f}")
                    else:
                        self.temp_labels[key].setText("--")
                
                # Update current display  
                if key in self.current_labels:
                    if current > 0:
                        self.current_labels[key].setText(f"{current:.2f}")
                    else:
                        self.current_labels[key].setText("--")
                
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

"""
PR59 Temperature Controller Widget for BVEX Ground Station
Clean display of PR59 telemetry parameters from the temperature controller
"""

import sys
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QApplication, QPushButton)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from datetime import datetime

from src.data.pr59_client import PR59Client, PR59Data


class StatusIndicator(QLabel):
    """Custom widget to display colored indicator for running status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = False
        self.setFixedSize(12, 12)
    
    def set_status(self, is_running):
        """Set the status and update the display"""
        self.is_running = is_running
        self.update()
    
    def paintEvent(self, event):
        """Paint the colored indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Choose color based on status
        if self.is_running:
            color = QColor(40, 167, 69)  # Green for running
        else:
            color = QColor(220, 53, 69)  # Red for stopped
        
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawEllipse(1, 1, 10, 10)


class PR59Widget(QWidget):
    """Clean widget for displaying PR59 temperature controller telemetry"""
    
    def __init__(self, parent=None, server_ip="127.0.0.1", server_port=8082):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize PR59 client
        self.pr59_client = PR59Client(server_ip=server_ip, server_port=server_port)
        
        # Control state - start OFF by default to save resources
        self.is_active = False
        
        # Setup the UI
        self.setup_ui()
        
        self.logger.info("PR59 Widget initialized (OFF by default)")
    
    def setup_ui(self):
        """Initialize the clean user interface matching GPS/Motor Controller style"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("PR59 Controller: OFF")
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
        
        # Create the main container with clean styling like GPS widget
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
        
        # Set proper size - similar to PBoB widget
        self.setMinimumSize(650, 350)
        self.setMaximumSize(750, 420)
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_pr59_controller()
        else:
            self.start_pr59_controller()
    
    def start_pr59_controller(self):
        """Start PR59 controller telemetry updates"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("PR59 Controller: ON")
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
            
            # Start update timer - SIMPLE approach like other widgets
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_display)
            self.update_timer.start(1000)  # Update every second
    
    def stop_pr59_controller(self):
        """Stop PR59 controller telemetry updates"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("PR59 Controller: OFF")
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
            
            # Stop update timer - SIMPLE approach like other widgets
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            
            # Show static display
            self.setup_static_display()
    
    def setup_static_display(self):
        """Setup static display when PR59 controller is OFF"""
        # Clear current layout more safely without processEvents()
        if hasattr(self, 'container_layout') and self.container_layout is not None:
            # Clear layout safely using a simple approach
            for i in reversed(range(self.container_layout.count())):
                child = self.container_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
        
        # Ensure we have a valid container layout
        if not hasattr(self, 'container_layout') or self.container_layout is None:
            return
        
        # Static message
        static_label = QLabel("PR59 Temperature Controller")
        static_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        static_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        static_label.setStyleSheet("QLabel { color: #6c757d; padding: 20px; }")
        
        info_label = QLabel("Turn ON to monitor PR59 telemetry\n\n• PID Control Parameters\n• Temperature Readings\n• Power Measurements\n• Controller Status")
        info_label.setFont(QFont("Arial", 11))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("QLabel { color: #868e96; line-height: 1.4; }")
        
        self.container_layout.addWidget(static_label)
        self.container_layout.addWidget(info_label)
        self.container_layout.addStretch()

    def setup_active_display(self):
        """Setup the active PR59 telemetry display with clean grid layout"""
        # Clear current layout
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Status header like motor controller widget
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main data section
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
    
    def _create_status_header(self):
        """Create clean connection status header like motor controller widget"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.NoFrame)
        header.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
                border-bottom: 1px solid #dee2e6;
                padding: 1px;
                margin: 1px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(5, 1, 5, 1)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel("🌡️ PR59 Temperature Controller")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("QLabel { color: #495057; }")
        
        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connection_label.setStyleSheet("QLabel { color: red; }")
        
        # Last update time
        self.last_update_label = QLabel("Last Update: Never")
        self.last_update_label.setFont(QFont("Arial", 9))
        self.last_update_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.connection_label)
        layout.addStretch()
        layout.addWidget(self.last_update_label)
        
        return header
    
    def _create_data_section(self):
        """Create the main data display section with clean grid layout"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use a grid layout for organized display
        layout = QGridLayout(data_frame)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create field labels storage
        self.field_labels = {}
        self.status_indicator = None
        
        # PR59 telemetry parameters organized by category
        row = 0
        
        # PID Parameters section
        pid_header = QLabel("PID Control Parameters:")
        pid_header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        pid_header.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; margin-top: 5px; }")
        layout.addWidget(pid_header, row, 0, 1, 4)
        row += 1
        
        pid_params = [
            ("Proportional (Kp):", "kp", ""),
            ("Integral (Ki):", "ki", ""),
            ("Derivative (Kd):", "kd", "")
        ]
        
        for i, (label_text, field, unit) in enumerate(pid_params):
            col = (i % 2) * 2  # Arrange in 2 columns
            if i == 2:  # Third item goes to second row
                row += 1
                col = 0
            
            # Parameter label
            param_label = QLabel(label_text)
            param_label.setFont(QFont("Arial", 10))
            param_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            param_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            param_label.setMaximumWidth(120)
            layout.addWidget(param_label, row, col)
            
            # Value label
            value_label = QLabel("--")
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
            value_label.setMinimumWidth(80)
            layout.addWidget(value_label, row, col + 1)
            
            self.field_labels[field] = value_label
        
        row += 2  # Add some spacing
        
        # Temperature section
        temp_header = QLabel("Temperature Readings:")
        temp_header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        temp_header.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; margin-top: 5px; }")
        layout.addWidget(temp_header, row, 0, 1, 4)
        row += 1
        
        temp_params = [
            ("Temperature:", "temp", "°C"),
            ("FET Temperature:", "fet_temp", "°C")
        ]
        
        for i, (label_text, field, unit) in enumerate(temp_params):
            col = i * 2
            
            # Parameter label
            param_label = QLabel(label_text)
            param_label.setFont(QFont("Arial", 10))
            param_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            param_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            param_label.setMaximumWidth(120)
            layout.addWidget(param_label, row, col)
            
            # Value label
            value_label = QLabel(f"-- {unit}")
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
            value_label.setMinimumWidth(80)
            layout.addWidget(value_label, row, col + 1)
            
            self.field_labels[field] = value_label
        
        row += 2  # Add some spacing
        
        # Power section
        power_header = QLabel("Power Measurements:")
        power_header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        power_header.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; margin-top: 5px; }")
        layout.addWidget(power_header, row, 0, 1, 4)
        row += 1
        
        power_params = [
            ("Current:", "current", "A"),
            ("Voltage:", "voltage", "V"),
            ("Power:", "power", "W")
        ]
        
        for i, (label_text, field, unit) in enumerate(power_params):
            col = (i % 2) * 2  # Arrange in 2 columns
            if i == 2:  # Third item goes to second row
                row += 1
                col = 0
            
            # Parameter label
            param_label = QLabel(label_text)
            param_label.setFont(QFont("Arial", 10))
            param_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            param_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            param_label.setMaximumWidth(120)
            layout.addWidget(param_label, row, col)
            
            # Value label
            value_label = QLabel(f"-- {unit}")
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
            value_label.setMinimumWidth(80)
            layout.addWidget(value_label, row, col + 1)
            
            self.field_labels[field] = value_label
        
        row += 2  # Add some spacing
        
        # Status section
        status_header = QLabel("Controller Status:")
        status_header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        status_header.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; margin-top: 5px; }")
        layout.addWidget(status_header, row, 0, 1, 4)
        row += 1
        
        # Running status with indicator
        running_label = QLabel("Running:")
        running_label.setFont(QFont("Arial", 10))
        running_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        running_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        running_label.setMaximumWidth(120)
        layout.addWidget(running_label, row, 0)
        
        # Status indicator
        self.status_indicator = StatusIndicator()
        layout.addWidget(self.status_indicator, row, 1, Qt.AlignmentFlag.AlignLeft)
        
        # Status text
        status_text_label = QLabel("Status:")
        status_text_label.setFont(QFont("Arial", 10))
        status_text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_text_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        status_text_label.setMaximumWidth(120)
        layout.addWidget(status_text_label, row, 2)
        
        # Status value label
        status_value_label = QLabel("N/A")
        status_value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
        status_value_label.setMinimumWidth(80)
        layout.addWidget(status_value_label, row, 3)
        
        self.field_labels["status"] = status_value_label
        
        row += 1  # Move to next row for fan status
        
        # Fan status field
        fan_status_label = QLabel("Fan Status:")
        fan_status_label.setFont(QFont("Arial", 10))
        fan_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        fan_status_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        fan_status_label.setMaximumWidth(120)
        layout.addWidget(fan_status_label, row, 0)
        
        # Fan status value label
        fan_status_value_label = QLabel("N/A")
        fan_status_value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        fan_status_value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        fan_status_value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
        fan_status_value_label.setMinimumWidth(80)
        layout.addWidget(fan_status_value_label, row, 1)
        
        self.field_labels["fan_status"] = fan_status_value_label
        
        return data_frame
    
    def update_display(self):
        """Update the display with current data (only when active)"""
        if not self.is_active:
            return
            
        try:
            # Update data from client
            self.pr59_client.update_data()
            data = self.pr59_client.get_data()
            
            # Update connection status
            status = self.pr59_client.get_connection_status()
            self.connection_label.setText(status)
            if status == "Connected":
                self.connection_label.setStyleSheet("QLabel { color: green; }")
            elif status == "Connecting...":
                self.connection_label.setStyleSheet("QLabel { color: orange; }")
            elif status == "Unauthorized":
                self.connection_label.setStyleSheet("QLabel { color: orange; }")
            else:
                self.connection_label.setStyleSheet("QLabel { color: red; }")
            
            if data.valid:
                # Update last update time
                current_time = datetime.now().strftime("%H:%M:%S")
                self.last_update_label.setText(f"Last Update: {current_time}")
                
                # Update PID parameters
                self.field_labels["kp"].setText(f"{data.kp:.4f}")
                self.field_labels["ki"].setText(f"{data.ki:.4f}")
                self.field_labels["kd"].setText(f"{data.kd:.4f}")
                
                # Update temperature readings with color coding
                self._update_temperature_field("temp", data.temp, "°C")
                self._update_temperature_field("fet_temp", data.fet_temp, "°C")
                
                # Update power measurements
                self._update_power_field("current", data.current, "A")
                self._update_power_field("voltage", data.voltage, "V")
                self._update_power_field("power", data.power, "W")
                
                # Update status
                self.status_indicator.set_status(data.running == 1)
                self.field_labels["status"].setText(data.status)
                
                # Update fan status with color coding
                self._update_fan_status_field(data.fan_status)
                
            else:
                # Check if server is responding (even if unauthorized)
                if self.pr59_client.is_server_responding():
                    self.last_update_label.setText("Last Update: Server responding (auth required)")
                else:
                    self.last_update_label.setText("Last Update: No data")
                
                # Reset all displays
                for field in ["kp", "ki", "kd"]:
                    self.field_labels[field].setText("--")
                    self.field_labels[field].setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
                
                for field, unit in [("temp", "°C"), ("fet_temp", "°C"), ("current", "A"), ("voltage", "V"), ("power", "W")]:
                    self.field_labels[field].setText(f"-- {unit}")
                    self.field_labels[field].setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
                
                self.status_indicator.set_status(False)
                if self.pr59_client.is_server_responding():
                    self.field_labels["status"].setText("Auth Required")
                    self.field_labels["status"].setStyleSheet("QLabel { color: #ffc107; border: none; background: transparent; }")
                else:
                    self.field_labels["status"].setText("N/A")
                    self.field_labels["status"].setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
                
                # Reset fan status when no data
                self.field_labels["fan_status"].setText("N/A")
                self.field_labels["fan_status"].setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
                    
        except Exception as e:
            self.logger.error(f"Error updating PR59 display: {e}")
            self.connection_label.setText("Error")
            self.connection_label.setStyleSheet("QLabel { color: red; }")
    
    def _update_temperature_field(self, field, value, unit):
        """Update temperature field with color coding"""
        label = self.field_labels[field]
        label.setText(f"{value:.2f} {unit}")
        
        # Color code based on temperature ranges (example thresholds)
        if value > 50.0:  # High temperature
            label.setStyleSheet("QLabel { color: #dc3545; font-weight: bold; border: none; background: transparent; }")
        elif value > 30.0:  # Medium temperature
            label.setStyleSheet("QLabel { color: #ffc107; font-weight: bold; border: none; background: transparent; }")
        else:  # Normal temperature
            label.setStyleSheet("QLabel { color: #28a745; border: none; background: transparent; }")
    
    def _update_power_field(self, field, value, unit):
        """Update power field with color coding"""
        label = self.field_labels[field]
        label.setText(f"{value:.3f} {unit}")
        
        # Color code based on power consumption (example thresholds)
        if field == "current" and value > 1.0:  # High current
            label.setStyleSheet("QLabel { color: #dc3545; font-weight: bold; border: none; background: transparent; }")
        elif field == "power" and value > 5.0:  # High power
            label.setStyleSheet("QLabel { color: #dc3545; font-weight: bold; border: none; background: transparent; }")
        elif field == "voltage" and (value < 10.0 or value > 15.0):  # Voltage out of normal range
            label.setStyleSheet("QLabel { color: #ffc107; font-weight: bold; border: none; background: transparent; }")
        else:  # Normal values
            label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
    
    def _update_fan_status_field(self, fan_status_value):
        """Update fan status field with color coding based on updated guide values"""
        label = self.field_labels["fan_status"]
        label.setText(fan_status_value)
        
        # Color code based on fan status values from the updated guide
        if fan_status_value == "automatic":
            # Normal operation - green
            label.setStyleSheet("QLabel { color: #28a745; font-weight: bold; border: none; background: transparent; }")
        elif fan_status_value == "forced_on":
            # Fan manually forced ON - blue/info color
            label.setStyleSheet("QLabel { color: #17a2b8; font-weight: bold; border: none; background: transparent; }")
        elif fan_status_value == "forced_off":
            # Fan manually forced OFF - warning orange
            label.setStyleSheet("QLabel { color: #ffc107; font-weight: bold; border: none; background: transparent; }")
        elif fan_status_value == "N/A":
            # PR59 not running or data unavailable - gray
            label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        else:
            # Invalid/unknown status - show as error in red with the actual value
            label.setStyleSheet("QLabel { color: #dc3545; font-weight: bold; border: none; background: transparent; }")

    def cleanup(self):
        """Clean up resources"""
        # Stop our timer - SIMPLE approach like other widgets
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Cleanup client
        if hasattr(self, 'pr59_client'):
            self.pr59_client.cleanup()
        
        self.logger.info("PR59 Widget cleanup completed") 
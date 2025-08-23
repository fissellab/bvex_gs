"""
Heater System Widget for BVEX Ground Station
Read-only display of heater telemetry and system status according to HEATER_CLIENT_GUIDE.md
"""

import sys
import logging
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QApplication, QPushButton)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from datetime import datetime

from src.data.heater_client import HeaterTelemetryClient, HeaterData
from src.config.settings import HEATER_TELEMETRY


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
    """Read-only widget for displaying heater telemetry and system status"""
    
    def __init__(self, parent=None, server_ip=None, server_port=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize telemetry client only (no control capabilities)
        self.telemetry_client = HeaterTelemetryClient(
            host=server_ip or HEATER_TELEMETRY['host'],
            port=server_port or HEATER_TELEMETRY['port']
        )
        
        # Current data storage
        self.current_data = HeaterData()
        
        # Control state - start OFF by default to save resources
        self.is_active = False
        
        # Setup the UI
        self.setup_ui()
        
        self.logger.info("Heater Widget initialized (display-only mode)")
    
    def setup_ui(self):
        """Initialize the read-only telemetry display interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Header panel (read-only status)
        header_layout = QHBoxLayout()
        
        # System status label
        self.system_status_label = QLabel("Heater Telemetry: Ready")
        self.system_status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.system_status_label.setStyleSheet("QLabel { color: #28a745; }")
        
        # Toggle button for widget activation (display only)
        self.toggle_button = QPushButton("Start Monitoring")
        self.toggle_button.setMinimumWidth(120)
        self.toggle_button.clicked.connect(self.toggle_monitoring)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        header_layout.addWidget(self.system_status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(header_layout)
        
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
        
        # Set proper size to match other widgets
        self.setMinimumSize(600, 300)
        self.setMaximumSize(800, 400)
    
    def toggle_monitoring(self):
        """Toggle between monitoring on/off (display only)"""
        if self.is_active:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start heater telemetry monitoring (read-only)"""
        self.is_active = True
        self.system_status_label.setText("Heater Telemetry: Monitoring")
        self.system_status_label.setStyleSheet("QLabel { color: #28a745; }")
        self.toggle_button.setText("Stop Monitoring")
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
        
        # Setup active telemetry display
        self.setup_telemetry_display()
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(2000)  # Update every 2 seconds
        
        self.logger.info("Heater telemetry monitoring started")
    
    def stop_monitoring(self):
        """Stop heater telemetry monitoring"""
        try:
            self.is_active = False
            self.system_status_label.setText("Heater Telemetry: Ready")
            self.system_status_label.setStyleSheet("QLabel { color: #6c757d; }")
            self.toggle_button.setText("Start Monitoring")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            
            # Stop update timer safely
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
                self.update_timer.deleteLater()
                self.update_timer = None
            
            # Setup static display
            self.setup_static_display()
            
            self.logger.info("Heater telemetry monitoring stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping heater monitoring: {e}")
    
    def setup_static_display(self):
        """Setup static display when widget is OFF"""
        # Ensure container_layout exists
        if not hasattr(self, 'container_layout') or self.container_layout is None:
            return
            
        # Clear existing layout safely
        for i in reversed(range(self.container_layout.count())):
            item = self.container_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.container_layout.removeItem(item)
        
        # Static message like other widgets
        static_label = QLabel("Heater System Telemetry")
        static_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        static_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        static_label.setStyleSheet("QLabel { color: #6c757d; padding: 20px; }")
        
        info_label = QLabel("Start Monitoring to view heater telemetry\n\n• Temperature readings for all heaters\n• Current consumption tracking\n• ON/OFF status indicators\n• System current limit monitoring (3A)")
        info_label.setFont(QFont("Arial", 11))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("QLabel { color: #868e96; line-height: 1.4; }")
        
        self.container_layout.addWidget(static_label)
        self.container_layout.addWidget(info_label)
        self.container_layout.addStretch()
    
    def setup_telemetry_display(self):
        """Setup active heater telemetry display (read-only)"""
        # Ensure container_layout exists
        if not hasattr(self, 'container_layout') or self.container_layout is None:
            return
            
        # Clear existing layout safely
        for i in reversed(range(self.container_layout.count())):
            item = self.container_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.container_layout.removeItem(item)
        
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main telemetry section
        telemetry_section = self._create_telemetry_section()
        self.container_layout.addWidget(telemetry_section)
    
    def _create_status_header(self):
        """Create clean connection status header like other widgets"""
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
        title_label = QLabel("Heater System Telemetry")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("QLabel { color: #495057; }")
        
        # Connection status
        self.connection_status_label = QLabel("Disconnected")
        self.connection_status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connection_status_label.setStyleSheet("QLabel { color: red; }")
        
        # Last update time like other widgets
        self.last_update_label = QLabel("Last Update: Never")
        self.last_update_label.setFont(QFont("Arial", 9))
        self.last_update_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.connection_status_label)
        layout.addStretch()
        layout.addWidget(self.last_update_label)
        
        return header
    
    # Static info section method removed - using simplified static display like other widgets
    
    def _create_telemetry_section(self):
        """Create the main telemetry display section (read-only)"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use a grid layout for organized display like other widgets
        layout = QGridLayout(data_frame)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 6, 10, 6)
        
        # Create field labels for telemetry display
        self.status_indicators = {}
        self.temp_labels = {}
        self.current_labels = {}
        
        # Section header
        header_label = QLabel("Individual Heater Status:")
        header_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; margin-top: 5px; }")
        layout.addWidget(header_label, 0, 0, 1, 4)
        
        # Column headers (cleaner layout)
        headers = ["Component", "Status", "Temp (°C)", "Current (A)"]
        for col, header in enumerate(headers):
            col_label = QLabel(header)
            col_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            col_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; padding: 2px; }")
            col_label.setAlignment(Qt.AlignmentFlag.AlignCenter if col > 0 else Qt.AlignmentFlag.AlignLeft)
            col_label.setMinimumHeight(20)
            layout.addWidget(col_label, 1, col)
        
        # Heater definitions according to guide (telemetry channels)
        heaters = [
            ("Star Camera", "starcam", "Auto (25-30°C)"),
            ("Motor", "motor", "Auto (25-30°C)"),
            ("Ethernet Switch", "ethernet", "Auto (25-30°C)"),
            ("Lock Pin", "lockpin", "Auto (25-30°C)"),
            ("Pressure Vessel", "spare", "Manual Only")
        ]
        
        row = 2  # Start after header and column labels
        for heater_name, heater_key, heater_type in heaters:
            # Component name
            name_label = QLabel(f"{heater_name}")
            name_label.setFont(QFont("Arial", 10))
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; padding: 3px; }")
            name_label.setMinimumWidth(100)
            layout.addWidget(name_label, row, 0)
            
            # Status indicator
            indicator = StatusIndicator()
            layout.addWidget(indicator, row, 1, Qt.AlignmentFlag.AlignCenter)
            self.status_indicators[heater_key] = indicator
            
            # Temperature display
            temp_label = QLabel("--")
            temp_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            temp_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; padding: 3px; }")
            temp_label.setMinimumWidth(70)
            layout.addWidget(temp_label, row, 2)
            self.temp_labels[heater_key] = temp_label
            
            # Current display
            current_label = QLabel("--")
            current_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            current_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; padding: 3px; }")
            current_label.setMinimumWidth(70)
            layout.addWidget(current_label, row, 3)
            self.current_labels[heater_key] = current_label
            
            row += 1
        
        # Add spacing
        row += 1
        
        # System status section header
        system_header = QLabel("System Status:")
        system_header.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        system_header.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; margin-top: 8px; }")
        layout.addWidget(system_header, row, 0, 1, 4)
        row += 1
        
        # System running status
        sys_status_label = QLabel("Running:")
        sys_status_label.setFont(QFont("Arial", 10))
        sys_status_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; padding: 3px; }")
        layout.addWidget(sys_status_label, row, 0)
        
        self.heater_system_status_label = QLabel("Unknown")
        self.heater_system_status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.heater_system_status_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; padding: 3px; }")
        layout.addWidget(self.heater_system_status_label, row, 1)
        
        # Total current display
        current_status_label = QLabel("Total Current:")
        current_status_label.setFont(QFont("Arial", 10))
        current_status_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; padding: 3px; }")
        layout.addWidget(current_status_label, row, 2)
        
        self.total_current_label = QLabel("-- A")
        self.total_current_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.total_current_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; padding: 3px; }")
        layout.addWidget(self.total_current_label, row, 3)
        
        return data_frame
    
    # Toggle methods removed - widget is now display-only according to HEATER_CLIENT_GUIDE.md
    # Heater control is handled via BCP command interface on port 8090, not through GUI
    
    def update_display(self):
        """Update the display with current telemetry data"""
        if not self.is_active:
            return
        
        try:
            # Get current telemetry data
            self.update_telemetry_data()
            
            # Update connection status based on recent telemetry success
            if self.current_data.valid:
                self.connection_status_label.setText("Connected")
                self.connection_status_label.setStyleSheet("QLabel { color: #28a745; }")
            else:
                self.connection_status_label.setText("Disconnected")
                self.connection_status_label.setStyleSheet("QLabel { color: #dc3545; }")
            
            # Update heater system running status
            if self.current_data.system_running:
                self.heater_system_status_label.setText("Yes")
                self.heater_system_status_label.setStyleSheet("QLabel { color: #28a745; border: none; background: transparent; padding: 3px; }")
            else:
                self.heater_system_status_label.setText("No")
                self.heater_system_status_label.setStyleSheet("QLabel { color: #ffc107; border: none; background: transparent; padding: 3px; }")
            
            # Update total current
            if self.current_data.total_current > 0:
                current_color = "#dc3545" if self.current_data.total_current > 2.5 else "#28a745"  # Red if near 3A limit
                self.total_current_label.setText(f"{self.current_data.total_current:.2f} A")
                self.total_current_label.setStyleSheet(f"QLabel {{ color: {current_color}; border: none; background: transparent; padding: 3px; }}")
            else:
                self.total_current_label.setText("-- A")
                self.total_current_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; padding: 3px; }")
            
            # Update last update time
            if hasattr(self, 'last_update_label'):
                self.last_update_label.setText(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
            
            # Update individual heater status indicators and telemetry
            heater_data_map = {
                'starcam': (self.current_data.starcam_state, self.current_data.starcam_temp, self.current_data.starcam_current),
                'motor': (self.current_data.motor_state, self.current_data.motor_temp, self.current_data.motor_current),
                'ethernet': (self.current_data.ethernet_state, self.current_data.ethernet_temp, self.current_data.ethernet_current),
                'lockpin': (self.current_data.lockpin_state, self.current_data.lockpin_temp, self.current_data.lockpin_current),
                'spare': (self.current_data.spare_state, self.current_data.spare_temp, self.current_data.spare_current)
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
    
    def update_telemetry_data(self):
        """Update heater data from telemetry system"""
        try:
            # Get comprehensive status from telemetry
            status = self.telemetry_client.get_heater_status()
            
            # Update system status
            self.current_data.system_running = status.get('running', '0') == '1'
            
            try:
                self.current_data.total_current = float(status.get('total_current', '0'))
            except (ValueError, TypeError):
                self.current_data.total_current = 0.0
            
            # Update individual heater data
            heaters_map = {
                'starcam': 'starcam',
                'motor': 'motor', 
                'ethernet': 'ethernet',
                'lockpin': 'lockpin',
                'spare': 'spare'
            }
            
            for heater_key, data_attr in heaters_map.items():
                heater_data = status.get(heater_key, {})
                
                # Temperature
                try:
                    temp_val = float(heater_data.get('temp', '0'))
                    setattr(self.current_data, f'{data_attr}_temp', temp_val)
                except (ValueError, TypeError):
                    setattr(self.current_data, f'{data_attr}_temp', 0.0)
                
                # Current
                try:
                    current_val = float(heater_data.get('current', '0'))
                    setattr(self.current_data, f'{data_attr}_current', current_val)
                except (ValueError, TypeError):
                    setattr(self.current_data, f'{data_attr}_current', 0.0)
                
                # State
                state_str = heater_data.get('state', '-1')
                if state_str == '1':
                    setattr(self.current_data, f'{data_attr}_state', True)
                elif state_str == '0':
                    setattr(self.current_data, f'{data_attr}_state', False)
                else:
                    setattr(self.current_data, f'{data_attr}_state', None)
            
            self.current_data.valid = True
            self.current_data.timestamp = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating telemetry data: {e}")
            self.current_data.valid = False
            return False
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        try:
            self.logger.info("Starting heater widget cleanup...")
            
            # Stop monitoring gracefully
            if self.is_active:
                self.stop_monitoring()
            
            # Stop and clean up timer
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
                self.update_timer.deleteLater()
                self.update_timer = None
            
            # Clear data structures
            if hasattr(self, 'current_data'):
                self.current_data = None
            
            # Clear UI references
            if hasattr(self, 'status_indicators'):
                self.status_indicators.clear()
            if hasattr(self, 'temp_labels'):
                self.temp_labels.clear()
            if hasattr(self, 'current_labels'):
                self.current_labels.clear()
            
            # Telemetry client doesn't need explicit cleanup
            
            self.logger.info("Heater widget cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during heater widget cleanup: {e}")


# Test the widget standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = HeaterWidget()
    widget.show()
    
    sys.exit(app.exec()) 

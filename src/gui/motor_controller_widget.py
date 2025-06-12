"""
Motor Controller Display Widget for BVEX Ground Station
Displays motor controller and axis control telemetry (goes below GPS widget)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import time

from src.data.Oph_client import OphClient, OphData

class MotorControllerWidget(QWidget):
    """Widget for displaying motor controller and axis control telemetry"""
    
    def __init__(self, parent=None, oph_client=None):
        super().__init__(parent)
        
        # Use shared Ophiuchus client for telemetry if provided
        self.oph_client = oph_client if oph_client else OphClient()
        self.owns_client = oph_client is None  # Track if we own the client
        
        # Current data and state
        self.current_telemetry = OphData()
        self.is_active = False
        self.last_update_time = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the motor controller display interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Motor Controller: OFF")
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
        
        # Create the main container
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
        # Set proper size that fits content - increased height to show all fields properly
        self.setMinimumHeight(200)  # Significantly increased to show all 3 rows of data
        self.setMaximumHeight(220)  # Allow some flexibility
        self.setMinimumWidth(450)
        
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_motor_controller()
        else:
            self.start_motor_controller()
    
    def start_motor_controller(self):
        """Start motor controller telemetry updates"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("Motor Controller: ON")
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
            
            # Start Oph client if not already running (only if we own it)
            if self.owns_client and not self.oph_client.running:
                self.oph_client.start()
            # Always resume our client (shared or owned)
            self.oph_client.resume()
            
            # Setup active display
            self.setup_active_display()
            
            # Start update timer
            self.start_update_timer()
    
    def stop_motor_controller(self):
        """Stop motor controller telemetry updates"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("Motor Controller: OFF")
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
            
            # Pause Oph client
            self.oph_client.pause()
            
            # Stop update timer
            self.stop_update_timer()
            
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
        message_label = QLabel("Motor Controller - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start motor telemetry')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 10))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active motor controller display with all data fields"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main data section
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
    
    def _create_status_header(self):
        """Create motor controller connection status header"""
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
        
        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connection_label.setStyleSheet("QLabel { color: red; }")
        
        # Last update time
        self.last_update_label = QLabel("Last Update: Never")
        self.last_update_label.setFont(QFont("Arial", 9))
        self.last_update_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.connection_label)
        layout.addStretch()
        layout.addWidget(self.last_update_label)
        
        return header
    
    def _create_data_section(self):
        """Create the main data display section with motor controller and axis fields"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use a simple grid layout with clean spacing
        layout = QGridLayout(data_frame)
        layout.setSpacing(8)  # Increased spacing for better breathing room
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create all field labels
        self.field_labels = {}
        
        # Motor Controller and Axis Control fields - arranged in 4 columns (label-value pairs)
        fields = [
            # Row 1: Motor essentials
            ("mc_curr", "Motor Current", "A", 0, 0),
            ("mc_pos", "Motor Position", "deg", 0, 2),
            ("mc_vel", "Motor Velocity", "deg/s", 0, 4),
            ("mc_temp", "Motor Temp", "°C", 0, 6),
            
            # Row 2: Status and control
            ("ax_mode", "Axis Mode", "", 1, 0),
            ("ax_ot", "On Target", "", 1, 2),
            ("mc_sw", "Status Word", "", 1, 4),
            ("mc_np", "Network", "", 1, 6),
            
            # Row 3: Target controls
            ("ax_dest", "Target Elevation", "deg", 2, 0),
            ("ax_vel", "Target Velocity", "deg/s", 2, 2),
            ("ax_dest_az", "Target Azimuth", "deg", 2, 4),
            ("ax_vel_az", "Az Velocity", "deg/s", 2, 6),
        ]
        
        for field, label_text, unit, row, col in fields:
            # Create label with clean typography and word wrapping
            label = QLabel(f"{label_text}:")
            label.setFont(QFont("Arial", 9))
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            label.setWordWrap(True)  # Enable word wrapping for multi-word labels
            label.setMaximumWidth(80)  # Set a reasonable maximum width to force wrapping
            
            # Create value label with clean, no-border style like GPS widget
            value_label = QLabel("--")
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
            value_label.setMinimumWidth(60)
            
            # Add unit if specified
            if unit:
                display_text = f"-- {unit}"
                value_label.setText(display_text)
            
            # Add to layout
            layout.addWidget(label, row, col)
            layout.addWidget(value_label, row, col + 1)
            
            self.field_labels[field] = (value_label, unit)  # Store unit for updates
        
        return data_frame
    
    def start_update_timer(self):
        """Start the telemetry update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_telemetry)
        self.update_timer.start(1000)  # Update every second
    
    def stop_update_timer(self):
        """Stop the telemetry update timer"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
    
    def update_telemetry(self):
        """Update motor controller telemetry display"""
        if not self.is_active:
            return
        
        # Get current telemetry data
        telemetry = self.oph_client.get_data()
        self.current_telemetry = telemetry
        
        # Update connection status
        if telemetry.valid and self.oph_client.is_connected():
            self.connection_label.setText("Connected")
            self.connection_label.setStyleSheet("QLabel { color: green; }")
            self.last_update_time = time.time()
        else:
            self.connection_label.setText("Disconnected")
            self.connection_label.setStyleSheet("QLabel { color: red; }")
        
        # Update last update time
        if self.last_update_time:
            elapsed = time.time() - self.last_update_time
            if elapsed < 60:
                self.last_update_label.setText(f"Last Update: {elapsed:.1f}s ago")
            else:
                self.last_update_label.setText(f"Last Update: {elapsed/60:.1f}m ago")
        
        # Update all telemetry fields
        self._update_fields_display(telemetry)
    
    def _update_fields_display(self, telemetry: OphData):
        """Update all field displays with current telemetry data"""
        if not hasattr(self, 'field_labels'):
            return
        
        # Helper function to format values with units
        def update_field(field_key, value, format_str=None):
            if field_key in self.field_labels:
                label, unit = self.field_labels[field_key]
                if format_str:
                    display_value = format_str.format(value)
                else:
                    display_value = str(value)
                
                if unit:
                    label.setText(f"{display_value} {unit}")
                else:
                    label.setText(display_value)
        
        # Motor Controller fields
        update_field("mc_curr", telemetry.mc_curr, "{:.3f}")
        update_field("mc_pos", telemetry.mc_pos, "{:.2f}")
        update_field("mc_vel", telemetry.mc_vel, "{:.3f}")
        update_field("mc_temp", telemetry.mc_temp)
        update_field("mc_sw", telemetry.mc_sw)
        update_field("mc_np", telemetry.mc_np)
        
        # Axis Control fields
        mode_text = "Position" if telemetry.ax_mode == 1 else "Velocity"
        update_field("ax_mode", mode_text)
        update_field("ax_dest", telemetry.ax_dest, "{:.2f}")
        update_field("ax_vel", telemetry.ax_vel, "{:.3f}")
        update_field("ax_dest_az", telemetry.ax_dest_az, "{:.2f}")
        update_field("ax_vel_az", telemetry.ax_vel_az, "{:.3f}")
        ot_text = "Yes" if telemetry.ax_ot == 1 else "No"
        update_field("ax_ot", ot_text)
    
    def is_motor_controller_active(self) -> bool:
        """Check if motor controller display is active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Check if motor controller is connected"""
        return self.oph_client.is_connected()
    
    def get_current_telemetry(self) -> OphData:
        """Get current motor controller telemetry"""
        return self.current_telemetry 
"""
Motor Controller Display Widget for BVEX Ground Station
Displays motor controller and axis control telemetry (goes below GPS widget)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame, QPushButton, QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import time

from src.data.Oph_client import OphClient, OphData
from src.config.settings import GUI

class MotorControllerWidget(QWidget):
    """Widget for displaying motor controller and axis control telemetry"""
    
    def __init__(self, parent=None, oph_client=None):
        super().__init__(parent)
        
        # Create our own independent OphClient instance
        self.oph_client = OphClient()
        
        # Current data and state
        self.current_telemetry = OphData()
        self.is_active = False  # Start inactive by default
        self.last_update_time = None
        self.prev_mode = self.current_telemetry.ax_mode
        
        # Frequency control - default to 5 Hz
        self.update_frequency_hz = 10
        
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
        
        # Frequency dropdown
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["1 Hz", "5 Hz", "10 Hz"])
        self.frequency_combo.setCurrentText("10 Hz")  # Default to 10 Hz
        self.frequency_combo.setMinimumWidth(80)
        self.frequency_combo.setMaximumWidth(100)
        self.frequency_combo.currentTextChanged.connect(self.on_frequency_changed)
        self.frequency_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
                background-color: white;
                color: black;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                selection-background-color: #3daee9;
                selection-color: white;
            }
        """)
        
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
        control_layout.addWidget(self.frequency_combo)
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
            
            # Update frequency from current dropdown selection
            current_freq_text = self.frequency_combo.currentText()
            
            # Start our independent OphClient
            if self.oph_client.start():
                self.oph_client.resume()  # Ensure it's not paused
            
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
            
            # Stop update timer
            self.stop_update_timer()
            
            # Stop our independent OphClient
            self.oph_client.stop()
            
            # Show static display
            self.setup_static_display()
    
    def clear_widget(self,layout):
        """Recursively clear all widgets and layouts from the given layout"""
        for i in reversed(range(layout.count())):
            layoutItem = layout.itemAt(i)
            if layoutItem.widget() is not None:
                widgetToRemove = layoutItem.widget()
                widgetToRemove.setParent(None)
                layout.removeWidget(widgetToRemove)
            elif layoutItem.spacerItem() is not None:
                # Remove spacer item from layout
                layout.removeItem(layoutItem)
            else:
                # Handle nested layout
                layoutToRemove = layoutItem.layout()
                if layoutToRemove is not None:
                    # Recursively clear the nested layout
                    self.clear_widget(layoutToRemove)
                    # Remove the layout item from parent
                    layout.removeItem(layoutItem)

    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        self.clear_widget(self.container_layout)
        
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
        self.clear_widget(self.container_layout)
        
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
        if self.current_telemetry.ax_mode == 1:
            if GUI['lazisusan_enabled'] == 1:
                fields = [
                    ("ax_mode", "Mode", "", 0, 0),
                     # Row 1 and 2: Motor essentials
                    ("mc_curr", "Current", "A", 1, 0),
                    ("mc_pos", "Position", '°', 1, 2),
                    ("mc_vel", "Velocity", '°/s', 1, 4),
                
                    ("mc_temp", "Temp", "°C", 2, 0),
                    ("ax_dest", "Target EL", '°', 2, 2),
                    ("ax_dest_az", "Target AZ", '°', 2, 4),
            
                    # Row 3 and 4: Status
                    ("mc_lf", "Fault","", 3, 0),
                    ("mc_sw", "Status Word", "", 3, 2),
                    ("mc_sr", "Status Register", "", 3, 4),
                
                    ("mc_np", "Net Status", "", 4, 0),
                    ("mc_cww", "CW Write", "", 4, 2),
                    ("mc_cwr", "CW Read", "", 4, 4)
                    # Row 3: Target controls
                ]
            else:
                fields = [
                    ("ax_mode", "Mode", "", 0, 0),
                     # Row 1 and 2: Motor essentials
                    ("mc_curr", "Current", "A", 1, 0),
                    ("mc_pos", "Position", '°', 1, 2),
                    ("mc_vel", "Velocity", '°/s', 1, 4),
                
                    ("mc_temp", "Temp", "°C", 2, 0),
                    ("ax_dest", "Target EL", '°', 2, 2),
            
                    # Row 3 and 4: Status
                    ("mc_lf", "Fault","", 3, 0),
                    ("mc_sw", "Status Word", "", 3, 2),
                    ("mc_sr", "Status Register", "", 3, 4),
                
                    ("mc_np", "Net Status", "", 4, 0),
                    ("mc_cww", "CW Write", "", 4, 2),
                    ("mc_cwr", "CW Read", "", 4, 4)
                    # Row 3: Target controls
                ]
        else:
            if GUI['lazisusan_enabled'] == 1:
                fields = [
                    ("ax_mode", "Mode", "", 0, 0),
                     # Row 1 and 2: Motor essentials
                    ("mc_curr", "Current", "A", 1, 0),
                    ("mc_pos", "Position", '°', 1, 2),
                    ("mc_vel", "Velocity", '°/s', 1, 4),
                
                    ("mc_temp", "Temp", "°C", 2, 0),
                    ("ax_vel", "Target EL Vel", '°/s', 2, 2),
                    ("ax_vel_az", "Target AZ Vel", '°/s', 2, 4),
            
                    # Row 3 and 4: Status
                    ("mc_lf", "Fault", "",3, 0),
                    ("mc_sw", "Status Word", "", 3, 2),
                    ("mc_sr", "Status Register", "", 3, 4),
                
                    ("mc_np", "Net Status", "", 4, 0),
                    ("mc_cww", "CW Write", "", 4, 2),
                    ("mc_cwr", "CW Read", "", 4, 4)
                    # Row 3: Target controls
                ]
            else:
                fields = [
                    ("ax_mode", "Mode", "", 0, 0),
                     # Row 1 and 2: Motor essentials
                    ("mc_curr", "Current", "A", 1, 0),
                    ("mc_pos", "Position", '°', 1, 2),
                    ("mc_vel", "Velocity", '°/s', 1, 4),
                
                    ("mc_temp", "Temp", "°C", 2, 0),
                    ("ax_vel", "Target EL Vel", '°/s', 2, 2),
                    
            
                    # Row 3 and 4: Status
                    ("mc_lf", "Fault","", 3, 0),
                    ("mc_sw", "Status Word", "", 3, 2),
                    ("mc_sr", "Status Register", "", 3, 4),
                
                    ("mc_np", "Net Status", "", 4, 0),
                    ("mc_cww", "CW Write", "", 4, 2),
                    ("mc_cwr", "CW Read", "", 4, 4)
                    # Row 3: Target controls
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
        # Calculate interval in milliseconds based on selected frequency
        interval_ms = int(1000 / self.update_frequency_hz)
        self.update_timer.start(interval_ms)
    
    def stop_update_timer(self):
        """Stop the telemetry update timer"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
    
    def on_frequency_changed(self, frequency_text: str):
        """Handle frequency dropdown change"""
        # Extract the Hz value from the text (e.g., "5 Hz" -> 5)
        frequency_hz = int(frequency_text.split()[0])
        self.oph_client.set_metric_rate("mc",frequency_hz)
        
    
    def update_telemetry(self):
        """Update motor controller telemetry display"""
        if not self.is_active:
            return
        
        # Get current telemetry data from OphClient
        telemetry = self.oph_client.get_data()
        self.current_telemetry = telemetry
        
        # Update connection status - simplified logic
        if telemetry.valid and self.oph_client.is_connected():
            self.connection_label.setText("Connected")
            self.connection_label.setStyleSheet("QLabel { color: green; }")
            self.last_update_time = time.time()
        else:
            # Simple disconnected state
            self.connection_label.setText("Disconnected")
            self.connection_label.setStyleSheet("QLabel { color: red; }")
        
        # Update last update time
        if self.last_update_time:
            elapsed = time.time() - self.last_update_time
            if elapsed < 60:
                self.last_update_label.setText(f"Last Update: {elapsed:.1f}s ago")
            else:
                self.last_update_label.setText(f"Last Update: {elapsed/60:.1f}m ago")
        else:
            self.last_update_label.setText("Last Update: Never")
        
        # Update all telemetry fields
        self._update_fields_display(telemetry)
    
    def _update_fields_display(self, telemetry: OphData):
        """Update all field displays with current telemetry data"""
        if not hasattr(self, 'field_labels'):
            return
        if self.prev_mode != telemetry.ax_mode:
            self.setup_active_display()
            self.prev_mode = telemetry.ax_mode
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
        
        mode_text = "Position" if telemetry.ax_mode == 1 else "Velocity"
        update_field("ax_mode", mode_text)
        update_field("mc_curr", telemetry.mc_curr, "{:.2f}")
        update_field("mc_pos", telemetry.mc_pos, "{:.2f}")
        update_field("mc_vel", telemetry.mc_vel, "{:.2f}")
        update_field("mc_temp", telemetry.mc_temp)
        update_field("mc_sw", telemetry.mc_sw)
        update_field("mc_sr", telemetry.mc_sr)
        update_field("mc_np", telemetry.mc_np)
        update_field("mc_lf", telemetry.mc_lf)
        update_field("mc_cwr", telemetry.mc_cwr)
        update_field("mc_cww", telemetry.mc_cww)
        
        if telemetry.ax_mode == 1:
            update_field("ax_dest", telemetry.ax_dest, "{:.2f}")
            if GUI['lazisusan_enabled'] == 1:
                update_field("ax_dest_az", telemetry.ax_dest_az, "{:.2f}")
        else:
            update_field("ax_vel", telemetry.ax_vel, "{:.2f}")
            if GUI['lazisusan_enabled'] == 1:
                update_field("ax_vel_az", telemetry.ax_vel_az, "{:.2f}")
        
    
    def is_motor_controller_active(self) -> bool:
        """Check if motor controller display is active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Check if motor controller is connected"""
        return self.oph_client.is_connected()
    
    def get_current_telemetry(self) -> OphData:
        """Get current motor controller telemetry"""
        return self.current_telemetry
    
    def cleanup(self):
        """Clean up motor controller widget"""
        # Stop our timer
        self.stop_update_timer()
        
        # Stop our independent OphClient
        self.oph_client.stop() 

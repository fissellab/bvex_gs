"""
Scanning Operations Display Widget for BVEX Ground Station  
Displays scanning and target telemetry (goes below Star Camera widget)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QGridLayout, QFrame, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import time

from src.data.Oph_client import OphClient, OphData

class ScanningOperationsWidget(QWidget):
    """Widget for displaying scanning and target telemetry"""
    
    def __init__(self, parent=None, oph_client=None):
        super().__init__(parent)
        
        # Use shared Ophiuchus client for telemetry if provided
        self.oph_client = oph_client if oph_client else OphClient()
        self.owns_client = oph_client is None  # Track if we own the client
        
        # Current data and state
        self.current_telemetry = OphData()
        self.is_active = False
        self.last_update_time = None
        self.prev_mode = self.current_telemetry.scan_mode
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the scanning operations display interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Scanning Operations: OFF")
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
        self.container_layout.setSpacing(2)
        self.container_layout.setContentsMargins(4, 4, 4, 4)
        
        # Initially show static display
        self.setup_static_display()
        
        main_layout.addWidget(self.container)
        
        self.setLayout(main_layout)
        # Set proper size to show all data fields clearly - increased height for wrapped labels
        self.setMinimumSize(560, 220)  # Increased height to accommodate two-line labels
        self.setMaximumSize(640, 240)  # Allow some flexibility
        
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_scanning_operations()
        else:
            self.start_scanning_operations()
    
    def start_scanning_operations(self):
        """Start scanning operations telemetry updates"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("Scanning Operations: ON")
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
    
    def stop_scanning_operations(self):
        """Stop scanning operations telemetry updates"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("Scanning Operations: OFF")
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
        message_label = QLabel("Scanning Operations - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start scanning telemetry')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 10))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active scanning operations display with all data fields"""
        # Clear existing widgets
        self.clear_widget(self.container_layout)
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main data section
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
    
    def _create_status_header(self):
        """Create scanning operations connection status header"""
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
        """Create the main data display section with scanning and target fields"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use a simple grid layout with clean spacing
        layout = QGridLayout(data_frame)
        layout.setSpacing(8)  # Increased spacing for better breathing room
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create all field labels
        self.field_labels = {}
        
        # Scanning and Target fields - arranged in 4 columns (label-value pairs)
        if self.current_telemetry.scan_mode == 0:
            fields = [("scan_mode", "Mode","",0,0)]
        elif self.current_telemetry.scan_mode == 1:
            fields = [
                # Row 1: Scan mode
                ("scan_mode", "Mode", "", 0, 0),
                # Row 2: Scan parameters
                ("scan_start", "Start", "deg", 1, 0),
                ("scan_stop", "Stop", "deg", 1, 2),
                ("scan_vel", "Velocity", "deg/s", 1, 4),
            
                # Row 3: Scanning status
                ("scan_scan", "Scan", "", 2, 0),
                ("scan_nscans", "Total Scans", "", 2, 2)
            ]
        elif self.current_telemetry.scan_mode == 2:
            fields = [
                # Row 1: Scan mode
                ("scan_mode", "Mode","",0,0),
                # Row 2: Scan parameters
                ("target_lon", "RA", "deg", 1, 0),
                ("target_lat", "DEC", "deg", 1, 2),
                ("on_target", "On Target","", 0, 2),
                ("target_az", "AZ", "deg", 2, 0),
                ("target_el", "EL", "deg", 2, 2)
            ]
        elif self.current_telemetry.scan_mode == 3:
            fields = [
                # Row 1: Scan mode
                ("scan_mode", "Mode","",0,0),
                
                # Row 2:
                ("target_lon", "RA", "deg", 1, 0),
                ("target_lat", "DEC", "deg", 1, 2),
                ("scan_time", "Time", "s", 1, 4),
                
                #Row 3:
                ("scan_offset", "Offset", "deg", 2, 0),
                ("scan_op", "Operation", "", 2, 2),
                ("scan_scan", "Scan", "", 2, 4),
            ]
        
        for field, label_text, unit, row, col in fields:
            # Create label with clean typography and word wrapping
            label = QLabel(f"{label_text}:")
            label.setFont(QFont("Arial", 9))
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            label.setWordWrap(True)  # Enable word wrapping for multi-word labels
            label.setMaximumWidth(90)  # Slightly wider for scanning operations labels
            
            # Create value label with clean, no-border style like GPS widget
            value_label = QLabel("--")
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
            value_label.setMinimumWidth(70)
            
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
        """Update scanning operations telemetry display"""
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
        if telemetry.scan_mode != self.prev_mode:
            self.setup_active_display()
            self.prev_mode = telemetry.scan_mode
        
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
        
        # Scanning fields
        scan_modes = {0: "None", 1: "El Dither", 2: "Tracking", 3: "El On-Off"}
        mode_text = scan_modes.get(telemetry.scan_mode, "Unknown")
        update_field("scan_mode", mode_text)
        
        if telemetry.scan_mode == 1:
            update_field("scan_start", telemetry.scan_start, "{:.2f}")
            update_field("scan_stop", telemetry.scan_stop, "{:.2f}")
            update_field("scan_vel", telemetry.scan_vel, "{:.3f}")
            update_field("scan_scan", telemetry.scan_scan+1)
            update_field("scan_nscans", telemetry.scan_nscans)
            
        elif telemetry.scan_mode == 2:
            update_field("target_lon", telemetry.target_lon, "{:.4f}")
            update_field("target_lat", telemetry.target_lat, "{:.4f}")
            update_field("on_target",telemetry.ax_ot)
            update_field("target_az", telemetry.ax_dest, "{:.4f}")
            update_field("target_el", telemetry.ax_dest_az, "{:.4f}")
            
        elif telemetry.scan_mode == 3:
            update_field("scan_offset", telemetry.scan_offset, "{:.2f}")
            update_field("target_lon", telemetry.target_lon, "{:.4f}")
            update_field("target_lat", telemetry.target_lat, "{:.4f}")
            update_field("scan_scan", telemetry.scan_scan)
            update_field("scan_time", telemetry.scan_time, "{:.2f}")
            # Scan operation status
            scan_op_text = {-1: "Off Position", 0: "Moving", 1: "On Position"}.get(telemetry.scan_op, "Unknown")
            update_field("scan_op", scan_op_text)
    
    def is_scanning_operations_active(self) -> bool:
        """Check if scanning operations display is active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Check if scanning operations is connected"""
        return self.oph_client.is_connected()
    
    def get_current_telemetry(self) -> OphData:
        """Get current scanning operations telemetry"""
        return self.current_telemetry 

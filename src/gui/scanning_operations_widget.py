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
        self.setMinimumSize(560, 280)
        self.setMaximumSize(640, 320)
        
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
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
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
        data_frame.setStyleSheet("QFrame { background-color: white; }")
        
        # Use a simple grid layout
        layout = QGridLayout(data_frame)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Create all field labels
        self.field_labels = {}
        
        # Scanning and Target fields (arranged in 2 columns)
        fields = [
            # Scanning fields
            ("scan_mode", "Scan Mode", 0, 0),
            ("scan_start", "Scan Start (deg)", 0, 2),
            ("scan_stop", "Scan Stop (deg)", 1, 0),
            ("scan_vel", "Scan Velocity", 1, 2),
            ("scan_scan", "Current Scan", 2, 0),
            ("scan_nscans", "Total Scans", 2, 2),
            ("scan_offset", "Scan Offset", 3, 0),
            ("scan_op", "Scan Operation", 3, 2),
            
            # Target fields
            ("target_type", "Target Type", 4, 0),
            ("target_lon", "Target Longitude", 4, 2),
            ("target_lat", "Target Latitude", 5, 0),
            ("sc_save", "Star Camera Save", 5, 2),
        ]
        
        for field, label_text, row, col in fields:
            # Create label
            label = QLabel(f"{label_text}:")
            label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            label.setStyleSheet("QLabel { color: #333333; }")
            
            # Create value label
            value_label = QLabel("--")
            value_label.setFont(QFont("Arial", 9))
            value_label.setStyleSheet("QLabel { color: black; background-color: #f0f0f0; padding: 3px; border: 1px solid #ccc; }")
            value_label.setMinimumWidth(100)
            
            # Add to layout
            layout.addWidget(label, row, col)
            layout.addWidget(value_label, row, col + 1)
            
            self.field_labels[field] = value_label
        
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
        
        # Scanning fields
        scan_modes = {0: "None", 1: "El Dither", 2: "Tracking", 3: "El On-Off"}
        mode_text = scan_modes.get(telemetry.scan_mode, "Unknown")
        self.field_labels["scan_mode"].setText(mode_text)
        self.field_labels["scan_start"].setText(f"{telemetry.scan_start:.2f}")
        self.field_labels["scan_stop"].setText(f"{telemetry.scan_stop:.2f}")
        self.field_labels["scan_vel"].setText(f"{telemetry.scan_vel:.3f}")
        self.field_labels["scan_scan"].setText(f"{telemetry.scan_scan}")
        self.field_labels["scan_nscans"].setText(f"{telemetry.scan_nscans}")
        self.field_labels["scan_offset"].setText(f"{telemetry.scan_offset:.2f}")
        
        # Scan operation status
        scan_op_text = {-1: "Off Position", 0: "Moving", 1: "On Position"}.get(telemetry.scan_op, "Unknown")
        self.field_labels["scan_op"].setText(scan_op_text)
        
        # Target fields
        self.field_labels["target_type"].setText(telemetry.target_type)
        self.field_labels["target_lon"].setText(f"{telemetry.target_lon:.4f}")
        self.field_labels["target_lat"].setText(f"{telemetry.target_lat:.4f}")
        
        # Star Camera Save status
        save_text = "Recording" if telemetry.sc_save == 1 else "Not Recording"
        self.field_labels["sc_save"].setText(save_text)
    
    def is_scanning_operations_active(self) -> bool:
        """Check if scanning operations display is active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Check if scanning operations is connected"""
        return self.oph_client.is_connected()
    
    def get_current_telemetry(self) -> OphData:
        """Get current scanning operations telemetry"""
        return self.current_telemetry 
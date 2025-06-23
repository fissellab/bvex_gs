"""
Star Camera Status Widget for BVEX Ground Station
Displays telemetry data from the Ophiuchus server
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from src.data.Oph_client import OphClient, OphData


class StarCameraStatusWidget(QWidget):
    """Widget displaying star camera telemetry data from Ophiuchus"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize Ophiuchus client
        self.oph_client = OphClient()
        
        # Control state
        self.is_active = False
        
        # Current data
        self.current_data = OphData()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the star camera status interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Star Camera Status: OFF")
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
        self.setMinimumSize(600, 450)  # Increased size for better visibility
        
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_star_camera_status()
        else:
            self.start_star_camera_status()
    
    def start_star_camera_status(self):
        """Start star camera status updates"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("Star Camera Status: ON")
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
            
            # Start the client
            if self.oph_client.start():
                self.oph_client.resume()
                
                # Setup active display
                self.setup_active_display()
                
                # Start update timer
                self.start_update_timer()
                
                self.logger.info("Star camera status monitoring started")
            else:
                self.logger.error("Failed to start Ophiuchus client")
                self.stop_star_camera_status()
    
    def stop_star_camera_status(self):
        """Stop star camera status updates"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("Star Camera Status: OFF")
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
            
            # Stop the client
            self.oph_client.pause()
            self.oph_client.stop()
            
            # Setup static display
            self.setup_static_display()
            
            self.logger.info("Star camera status monitoring stopped")
    
    def setup_static_display(self):
        """Setup static display when not active"""
        # Clear current layout
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().setParent(None)
        
        # Add static message
        static_label = QLabel("Star Camera Status Monitoring Inactive")
        static_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        static_label.setFont(QFont("Arial", 14))
        static_label.setStyleSheet("QLabel { color: #666666; }")
        
        self.container_layout.addWidget(static_label)
        
    def setup_active_display(self):
        """Setup active display with telemetry data"""
        # Clear current layout
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().setParent(None)
        
        # Create grid layout for telemetry data
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)  # Increased spacing for better visibility
        grid_layout.setVerticalSpacing(8)  # Extra vertical spacing
        
        # Create data labels
        self.create_data_labels(grid_layout)
        
        # Add grid to container
        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        self.container_layout.addWidget(grid_widget)
        
        # Add connection status
        self.connection_status_label = QLabel("Connection: Disconnected")
        self.connection_status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Increased font size
        self.connection_status_label.setStyleSheet("QLabel { color: red; padding: 4px; }")
        self.container_layout.addWidget(self.connection_status_label)
        
        # Add data rate info
        self.data_rate_label = QLabel("Data Rate: 0.0 KB/s")
        self.data_rate_label.setFont(QFont("Arial", 11))  # Increased font size
        self.data_rate_label.setStyleSheet("QLabel { color: #000000; padding: 2px; }")  # Changed to black
        self.container_layout.addWidget(self.data_rate_label)
        
    def create_data_labels(self, grid_layout):
        """Create labels for displaying telemetry data"""
        
        # Define the data fields and their display names
        fields = [
            ('sc_ra', 'Right Ascension:', '°'),
            ('sc_dec', 'Declination:', '°'),
            ('sc_az', 'Azimuth:', '°'),
            ('sc_alt', 'Altitude:', '°'),
            ('sc_fr', 'Field Rotation:', '°'),
            ('sc_ir', 'Image Rotation:', '°'),
            ('sc_texp', 'Exposure Time:', 's'),
            ('sc_curr_focus', 'Current Focus:', ''),
            ('sc_start_focus', 'Start Focus:', ''),
            ('sc_end_focus', 'End Focus:', ''),
            ('sc_focus_step', 'Focus Step:', ''),
            ('sc_focus_mode', 'Focus Mode:', ''),
            ('sc_solve', 'Solve Mode:', ''),
            ('sc_save', 'Saving:', '')
        ]
        
        self.data_labels = {}
        
        for i, (field, display_name, unit) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            # Label for field name
            name_label = QLabel(display_name)
            name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Increased font size
            name_label.setStyleSheet("QLabel { color: #000000; padding: 2px; }")  # Black text with padding
            name_label.setMinimumWidth(120)  # Minimum width for label
            grid_layout.addWidget(name_label, row, col)
            
            # Label for field value
            value_label = QLabel(f"N/A {unit}".strip())
            value_label.setFont(QFont("Arial", 12))  # Increased font size
            value_label.setStyleSheet("QLabel { color: #000000; padding: 2px; background-color: #f0f0f0; border: 1px solid #ccc; }")  # Black text with light background
            value_label.setMinimumWidth(100)  # Minimum width for value
            grid_layout.addWidget(value_label, row, col + 1)
            
            self.data_labels[field] = value_label
    
    def start_update_timer(self):
        """Start the timer for periodic updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
    def stop_update_timer(self):
        """Stop the update timer"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
            self.update_timer = None
    
    def update_display(self):
        """Update the display with current telemetry data"""
        if not self.is_active:
            return
            
        # Get current data from client
        self.current_data = self.oph_client.get_data()
        
        # Update connection status
        if self.oph_client.is_connected():
            self.connection_status_label.setText("Connection: Connected")
            self.connection_status_label.setStyleSheet("QLabel { color: green; }")
        else:
            self.connection_status_label.setText("Connection: Disconnected")
            self.connection_status_label.setStyleSheet("QLabel { color: red; }")
        
        # Update data rate
        data_rate = self.oph_client.get_data_rate_kbps()
        self.data_rate_label.setText(f"Data Rate: {data_rate:.2f} KB/s")
        
        # Update data labels if data is valid
        if self.current_data.valid:
            self.update_data_labels()
        else:
            self.clear_data_labels()
    
    def update_data_labels(self):
        """Update data labels with current values"""
        data_dict = {
            'sc_ra': (self.current_data.sc_ra, '°', 2),
            'sc_dec': (self.current_data.sc_dec, '°', 2),
            'sc_az': (self.current_data.sc_az, '°', 2),
            'sc_alt': (self.current_data.sc_alt, '°', 2),
            'sc_fr': (self.current_data.sc_fr, '°', 2),
            'sc_ir': (self.current_data.sc_ir, '°', 2),
            'sc_texp': (self.current_data.sc_texp, 's', 3),
            'sc_curr_focus': (self.current_data.sc_curr_focus, '', 0),
            'sc_start_focus': (self.current_data.sc_start_focus, '', 0),
            'sc_end_focus': (self.current_data.sc_end_focus, '', 0),
            'sc_focus_step': (self.current_data.sc_focus_step, '', 0),
            'sc_focus_mode': (self.current_data.sc_focus_mode, '', 0),
            'sc_solve': (self.current_data.sc_solve, '', 0),
            'sc_save' : (self.current_data.sc_save,'',0)
        }
        
        for field, label in self.data_labels.items():
            if field in data_dict:
                value, unit, decimals = data_dict[field]
                if decimals > 0:
                    formatted_value = f"{value:.{decimals}f} {unit}".strip()
                else:
                    formatted_value = f"{int(value)} {unit}".strip()
                label.setText(formatted_value)
                label.setStyleSheet("QLabel { color: #000000; padding: 2px; background-color: #e8f5e8; border: 1px solid #4CAF50; }")  # Green background for valid data
    
    def clear_data_labels(self):
        """Clear data labels when no valid data"""
        for field, label in self.data_labels.items():
            if 'focus' in field or field in ['sc_solve', 'sc_focus_mode']:
                label.setText("N/A")
            else:
                label.setText("N/A °")
            label.setStyleSheet("QLabel { color: #000000; padding: 2px; background-color: #f0f0f0; border: 1px solid #ccc; }")  # Black text with light background
    
    def get_current_data(self) -> OphData:
        """Get current telemetry data"""
        return self.current_data
    
    def is_star_camera_status_active(self) -> bool:
        """Check if star camera status monitoring is active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Check if connected to Ophiuchus server"""
        return self.oph_client.is_connected() if hasattr(self, 'oph_client') else False 

"""
Gyroscope Display Widget for BVEX Ground Station
Compact display of gyroscope angular velocity data from BCP Sag system
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import time
import logging

from src.data.gyro_client import GyroClient, GyroData


class GyroWidget(QWidget):
    """Compact widget for displaying single-axis SPI gyroscope data from BCP Sag system"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create our own independent gyro client
        self.gyro_client = GyroClient()
        self.logger = logging.getLogger(__name__)
        
        self.last_gyro_data = GyroData()
        self.is_active = False  # Start OFF by default
        self.last_update_time = None
        
        # Frequency control - default to 10 Hz
        self.update_frequency_hz = 10
        
        self.setup_ui()
        
        # Setup update timer but don't start it yet
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gyro_display)
        
        self.logger.info("Gyro Widget initialized with independent GyroClient (OFF by default)")
        
    def setup_ui(self):
        """Setup the gyroscope display interface with clean, professional layout"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Gyroscope: OFF")
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
        # Make it much smaller and narrower to give motor controller breathing room
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_gyro_display()
        else:
            self.start_gyro_display()
    
    def start_gyro_display(self):
        """Start gyroscope display updates"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("Gyroscope: ON")
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
            
            # Setup active gyro display
            self.setup_active_display()
            
            # Start update timer based on frequency
            self.start_update_timer()
            
            self.logger.info("Gyro display started")
    
    def stop_gyro_display(self):
        """Stop gyroscope display updates and show static display"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("Gyroscope: OFF")
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
            
            # Show static display
            self.setup_static_display()
            
            self.logger.info("Gyro display stopped")
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add centered message - more compact for smaller widget
        message_label = QLabel("Gyro - Waiting")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON"')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 9))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active gyroscope display with all data fields"""
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
        """Create clean gyroscope connection status header"""
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
        """Create clean data section with single SPI gyro field"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Simple vertical layout for single value
        layout = QVBoxLayout(data_frame)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Single SPI gyro rate field - center aligned for clean look
        rate_layout = QHBoxLayout()
        
        # Label
        rate_label = QLabel("Rate:")
        rate_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        rate_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        
        # Value - larger font since it's the only value
        self.rate_value_label = QLabel("-- °/s")
        self.rate_value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.rate_value_label.setStyleSheet("color: #212529; border: none; background: transparent;")
        self.rate_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        rate_layout.addWidget(rate_label)
        rate_layout.addStretch()
        rate_layout.addWidget(self.rate_value_label)
        
        layout.addLayout(rate_layout)
        
        return data_frame
    
    def start_update_timer(self):
        """Start the gyroscope update timer"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_gyro_display)
        # Calculate interval in milliseconds based on selected frequency
        interval_ms = int(1000 / self.update_frequency_hz)
        self.update_timer.start(interval_ms)
        self.logger.debug(f"Started gyro update timer at {self.update_frequency_hz} Hz ({interval_ms}ms)")
    
    def stop_update_timer(self):
        """Stop the gyroscope update timer"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
    
    def on_frequency_changed(self, frequency_text: str):
        """Handle frequency dropdown change"""
        # Extract the Hz value from the text (e.g., "10 Hz" -> 10)
        self.update_frequency_hz = int(frequency_text.split()[0])
        
        # Restart timer with new frequency if active
        if self.is_active:
            self.start_update_timer()
        
        self.logger.debug(f"Gyro update frequency changed to {self.update_frequency_hz} Hz")
    
    def update_gyro_display(self):
        """Update gyroscope display with latest data"""
        if not self.is_active:
            return
        
        # Update data from gyro client
        success = self.gyro_client.update_data()
        gyro_data = self.gyro_client.get_data()
        self.last_gyro_data = gyro_data
        
        # Update connection status
        status = self.gyro_client.get_connection_status()
        self.connection_label.setText(status)
        if status == "Connected":
            self.connection_label.setStyleSheet("QLabel { color: green; }")
            self.last_update_time = time.time()
        elif status == "Connecting...":
            self.connection_label.setStyleSheet("QLabel { color: orange; }")
        else:
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
        
        # Update the single SPI gyro rate value
        if hasattr(self, 'rate_value_label'):
            if gyro_data.valid:
                # Show the actual rate value with high precision
                self.rate_value_label.setText(f"{gyro_data.spi_rate:.3f} °/s")
            else:
                # Show placeholder when no valid data
                self.rate_value_label.setText("-- °/s")
        
        # Force widget refresh
        self.update()
    
    def is_gyro_active(self) -> bool:
        """Return whether gyro display is currently active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Check if gyroscope client is connected"""
        return self.gyro_client.is_connected()
    
    def get_current_data(self) -> GyroData:
        """Get current gyroscope data"""
        return self.last_gyro_data
    
    def cleanup(self):
        """Clean up resources"""
        # Stop our timer
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        self.logger.info("Gyro widget cleaned up")

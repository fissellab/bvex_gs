"""
PBoB (Power Distribution Box) Widget for BVEX Ground Station
Clean display of relay states and current measurements for all subsystems
"""

import sys
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QApplication, QPushButton)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QColor
from datetime import datetime

from src.data.Oph_client import OphClient, OphData

class StatusCircle(QLabel):
    """Custom widget to display colored circle for ON/OFF status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_on = False
        self.setFixedSize(12, 12)  # Reduced from 16x16 to 12x12 for more compact display
    
    def set_status(self, is_on):
        """Set the status and update the display"""
        self.is_on = is_on
        self.update()
    
    def paintEvent(self, event):
        """Paint the colored circle"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Choose color based on status
        if self.is_on:
            color = QColor(40, 167, 69)  # Green
        else:
            color = QColor(220, 53, 69)  # Red
        
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawEllipse(1, 1, 10, 10)  # Adjusted circle size for smaller widget


class PBoBWidget(QWidget):
    """Clean widget for displaying Power Distribution Box (PBoB) relay states and current consumption"""
    
    def __init__(self, parent=None, oph_client=None):
        super().__init__(parent)
        
        # Create our own independent OphClient instance
        self.oph_client = OphClient()
        self.logger = logging.getLogger(__name__)
        
        # Control state - start OFF by default
        self.is_active = False
        
        # Setup the UI
        self.setup_ui()
        
        # Setup update timer but don't start it yet
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        self.logger.info("PBoB Widget initialized with independent OphClient (OFF by default)")
    
    def setup_ui(self):
        """Initialize the clean user interface matching GPS/Motor Controller style"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("PBoB Monitor: OFF")
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
        
        # Setup the active display (always show data)
        self.setup_active_display()
        
        main_layout.addWidget(self.container)
        
        # Set proper size - wider and adjusted height for better proportions
        self.setMinimumSize(650, 320)  # Increased width from 500 to 650
        self.setMaximumSize(750, 380)  # Increased width from 550 to 750
        
        # Initially show static display
        self.setup_static_display()
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_pbob_monitor()
        else:
            self.start_pbob_monitor()
    
    def start_pbob_monitor(self):
        """Start PBoB monitoring"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("PBoB Monitor: ON")
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
            
            # Start our independent OphClient
            if self.oph_client.start():
                self.oph_client.resume()  # Ensure it's not paused
                self.logger.info("PBoB OphClient started successfully")
            else:
                self.logger.error("Failed to start PBoB OphClient")
            
            # Setup active display
            self.setup_active_display()
            
            # Start update timer
            self.update_timer.start(1000)  # Update every second
    
    def stop_pbob_monitor(self):
        """Stop PBoB monitoring"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("PBoB Monitor: OFF")
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
            self.update_timer.stop()
            
            # Stop our independent OphClient
            self.oph_client.stop()
            
            # Show static display
            self.setup_static_display()
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        self.clear_widget(self.container_layout)
        
        # Add centered message
        message_label = QLabel("PBoB Monitor - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start power monitoring')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 10))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def clear_widget(self, layout):
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
    
    def setup_active_display(self):
        """Setup the active subsystem power display with clean grid layout"""
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
        title_label = QLabel("⚡ Subsystem Power")
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
        
        # Use a simple grid layout with tighter spacing for compact design
        layout = QGridLayout(data_frame)
        layout.setSpacing(6)  # Reduced from 8 to 6 for more compact layout
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Create field labels storage
        self.field_labels = {}
        self.status_circles = {}
        
        # Subsystem data - clean 3-column layout: Name, State (circle), Current
        # Added GPS (connected to relay 2 of PBoB 1)
        subsystems = [
            ("Star Camera", "sc_state", "sc_curr"),
            ("Motor", "m_state", "m_curr"),
            ("GPS", "gps_state", "gps_curr"),  # Added GPS subsystem
            ("Lock Pin", "lp_state", "lp_curr"),
            ("LNA", "lna_state", "lna_curr"),
            ("Mixer", "mix_state", "mix_curr"),
            ("RF SoC", "rfsoc_state", "rfsoc_curr")
        ]
        
        # Headers
        headers = ["Subsystem", "State", "Current"]
        for col, header in enumerate(headers):
            header_label = QLabel(f"{header}:")
            header_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            header_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
            if col == 0:
                header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            elif col == 1:
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header_label, 0, col)
        
        # Subsystem rows
        for row, (name, state_field, current_field) in enumerate(subsystems, 1):
            # Subsystem name label - clean typography
            name_label = QLabel(f"{name}:")
            name_label.setFont(QFont("Arial", 10))
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            name_label.setMaximumWidth(120)  # Increased from 100 to accommodate wider widget
            layout.addWidget(name_label, row, 0)
            
            # Status circle - more compact without extra widget wrapper
            circle = StatusCircle()
            layout.addWidget(circle, row, 1, Qt.AlignmentFlag.AlignCenter)
            
            # Current value label - clean, no-border style
            current_label = QLabel("-- A")
            current_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            current_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            current_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
            current_label.setMinimumWidth(80)
            layout.addWidget(current_label, row, 2)
            
            # Store references
            self.status_circles[state_field] = circle
            self.field_labels[current_field] = current_label
        
        # Set column stretch to distribute space better
        layout.setColumnStretch(0, 2)  # Subsystem name gets more space
        layout.setColumnStretch(1, 1)  # State column minimal space
        layout.setColumnStretch(2, 1)  # Current column moderate space
        
        return data_frame
    
    def update_display(self):
        """Update the display with current data"""
        if not self.is_active:
            return
            
        try:
            # Get data from OphClient
            data = self.oph_client.get_data()
            
            if data.valid and self.oph_client.is_connected():
                # Update connection status - simplified logic
                self.connection_label.setText("Connected")
                self.connection_label.setStyleSheet("QLabel { color: green; }")
                
                # Update last update time
                current_time = datetime.now().strftime("%H:%M:%S")
                self.last_update_label.setText(f"Last Update: {current_time}")
                
                # Update subsystem data
                subsystems = [
                    ("Star Camera", "sc_state", "sc_curr"),
                    ("Motor", "m_state", "m_curr"),
                    ("GPS", "gps_state", "gps_curr"),  # Added GPS subsystem
                    ("Lock Pin", "lp_state", "lp_curr"),
                    ("LNA", "lna_state", "lna_curr"),
                    ("Mixer", "mix_state", "mix_curr"),
                    ("RF SoC", "rfsoc_state", "rfsoc_curr")
                ]
                
                for name, state_field, current_field in subsystems:
                    # Update state circle
                    state_value = getattr(data, state_field, 0)
                    circle = self.status_circles[state_field]
                    circle.set_status(state_value == 1)
                    
                    # Update current
                    current_value = getattr(data, current_field, 0.0)
                    current_label = self.field_labels[current_field]
                    current_label.setText(f"{current_value:.3f} A")
                    
                    # Color code current based on value - like motor controller
                    if abs(current_value) > 0.1:
                        current_label.setStyleSheet("QLabel { color: #dc3545; font-weight: bold; border: none; background: transparent; }")
                    elif abs(current_value) > 0.05:
                        current_label.setStyleSheet("QLabel { color: #ffc107; font-weight: bold; border: none; background: transparent; }")
                    else:
                        current_label.setStyleSheet("QLabel { color: #28a745; border: none; background: transparent; }")
            else:
                # No valid data - simple disconnected state
                self.connection_label.setText("Disconnected")
                self.connection_label.setStyleSheet("QLabel { color: red; }")
                self.last_update_label.setText("Last Update: No data")
                
                # Reset all displays
                for state_field in self.status_circles:
                    circle = self.status_circles[state_field]
                    circle.set_status(False)  # All OFF
                    
                for current_field in self.field_labels:
                    current_label = self.field_labels[current_field]
                    current_label.setText("-- A")
                    current_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
                    
        except Exception as e:
            self.logger.error(f"Error updating PBoB display: {e}")
            self.connection_label.setText("Error")
            self.connection_label.setStyleSheet("QLabel { color: red; }")

    def cleanup(self):
        """Clean up resources"""
        # Stop our timer
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Stop our independent OphClient
        self.oph_client.stop()
        self.logger.info("PBoB OphClient stopped.")


# Test the widget standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create test widget
    widget = PBoBWidget()
    widget.show()
    
    sys.exit(app.exec()) 
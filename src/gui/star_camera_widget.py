"""
Star Camera Display Widget for BVEX Ground Station
Displays images from the star camera downlink server
"""

import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QPixmap, QImage
from PIL import Image
import datetime as dt
from collections import deque
import logging
import io
import time

from src.data.star_camera_client import StarCameraClient, StarCameraImage
from src.data.Oph_client import OphClient, OphData
from src.config.settings import STAR_CAMERA


class StarCameraWorker(QObject):
    """Worker to fetch star camera images in a separate thread"""
    image_updated = pyqtSignal(object)
    status_updated = pyqtSignal(object)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def fetch_image(self):
        """Fetch latest image from star camera"""
        try:
            # Check if we should attempt connection
            if not self.client.should_attempt_connection():
                # Return empty image without attempting connection
                self.image_updated.emit(StarCameraImage(0, 0, 0, 0, 0, 0, b'', False))
                return
                
            # Get server status first with short timeout
            status = self.client.get_status()
            if status and status.is_active:
                self.status_updated.emit(status)
                
                # Try to get an image only if server is responding
                image = self.client.get_latest_image()
                if image:
                    self.image_updated.emit(image)
                else:
                    # Emit empty image if request failed
                    self.image_updated.emit(StarCameraImage(0, 0, 0, 0, 0, 0, b'', False))
            else:
                # Server not responding, emit status and empty image
                self.status_updated.emit(status)
                self.image_updated.emit(StarCameraImage(0, 0, 0, 0, 0, 0, b'', False))
        except Exception as e:
            # Handle any unexpected errors gracefully
            self.image_updated.emit(StarCameraImage(0, 0, 0, 0, 0, 0, b'', False))
        
    def fetch_status(self):
        """Fetch server status"""
        try:
            # Always attempt status check, but with short timeout
            status = self.client.get_status()
            self.status_updated.emit(status)
        except Exception as e:
            # Emit disconnected status on error
            self.status_updated.emit(StarCameraStatus(0, 0, False, False, False))


class StarCameraWidget(QWidget):
    """Widget displaying star camera images"""
    trigger_fetch_image_signal = pyqtSignal()
    trigger_fetch_status_signal = pyqtSignal()

    def __init__(self, parent=None, oph_client=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        # Initialize star camera client (will be used in worker thread)
        self.star_camera_client = StarCameraClient()
        
        # Use shared Ophiuchus client for telemetry if provided
        self.oph_client = oph_client if oph_client else OphClient()
        self.owns_oph_client = oph_client is None  # Track if we own the client
        
        # Control state
        self.is_active = False
        
        # Data storage
        self.current_image = None
        self.current_status = None
        self.current_telemetry = OphData()
        self.last_fetch_time = None
        self.prev_focus_status = 0
        # History for data rate calculation
        self.update_times = deque(maxlen=10)
        
        self.setup_ui()
        self.setup_worker_thread()
        
    def setup_worker_thread(self):
        """Setup the worker thread for non-blocking data fetching"""
        self.worker_thread = QThread()
        self.worker = StarCameraWorker(self.star_camera_client)
        self.worker.moveToThread(self.worker_thread)

        self.worker.image_updated.connect(self.handle_image_update)
        self.worker.status_updated.connect(self.handle_status_update)
        self.trigger_fetch_image_signal.connect(self.worker.fetch_image)
        self.trigger_fetch_status_signal.connect(self.worker.fetch_status)

        self.worker_thread.start()
        
    def setup_ui(self):
        """Setup the star camera display interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Star Camera: OFF")
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
        control_layout.setSpacing(10)
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
        self.container_layout.setSpacing(10)
        self.container_layout.setContentsMargins(4, 4, 4, 4)
        
        # Initially show static display
        self.setup_static_display()
        
        main_layout.addWidget(self.container)
        
        self.setLayout(main_layout)
        self.setMinimumSize(560, 680)
        
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_star_camera()
        else:
            self.start_star_camera()
    
    def start_star_camera(self):
        """Start star camera image updates"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("Star Camera: ON")
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
            
            # Start the Ophiuchus client for telemetry (only if we own it)
            if self.owns_oph_client and not self.oph_client.running:
                self.oph_client.start()
            # Always resume our client (shared or owned)
            self.oph_client.resume()
            
            # Setup active display
            self.setup_active_display()
            
            # Start timers
            self.start_update_timers()
    
    def stop_star_camera(self):
        """Stop star camera updates and show static display"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("Star Camera: OFF")
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
            
            # Stop timers
            self.stop_update_timers()
            
            # Pause the Ophiuchus client, but only stop/cleanup if we own it
            self.oph_client.pause()
            if self.owns_oph_client:
                self.oph_client.stop()
                self.oph_client.cleanup()
            
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
                # Spacer item - no action needed, will be removed automatically
                pass
            else:
                layoutToRemove = layout.itemAt(i)
                self.clear_widget(layoutToRemove)

    """
        for i in reversed(range(layout.count())):
            if layout.itemAt(i) != None:
               if "Layout" not in str(layout.itemAt(i)):
                  if layout.itemAt(i).widget():
                      layout.itemAt(i).widget().setParent(None)
                      layout.removeWidget(layout.itemAt(i).widget())
               else:
                  self.clear_widget(layout.itemAt(i))
    """         
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        self.clear_widget(self.container_layout)
        
        # Add centered message
        message_label = QLabel("Star Camera Display - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start receiving images every 10 seconds')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 12))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        bandwidth_label = QLabel('(Limited to ~200 kB/s due to bandwidth constraints)')
        bandwidth_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bandwidth_label.setFont(QFont("Arial", 10))
        bandwidth_label.setStyleSheet("QLabel { color: #6c757d; font-style: italic; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addWidget(bandwidth_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Show active star camera display with image and controls"""
        # Clear existing widgets
        self.clear_widget(self.container_layout)
        
        # Simple clean status line at the top - no borders
        top_status_layout = QHBoxLayout()
        top_status_layout.setContentsMargins(5, 5, 5, 5)
        
        self.connection_status_label = QLabel("Status: Connecting...")
        self.connection_status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connection_status_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
        
        self.server_info_label = QLabel("Server: 100.85.84.122:8001")
        self.server_info_label.setFont(QFont("Arial", 10))
        self.server_info_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        
        top_status_layout.addWidget(self.connection_status_label)
        top_status_layout.addStretch()
        top_status_layout.addWidget(self.server_info_label)
        
        self.container_layout.addLayout(top_status_layout)
        
        # Image display section - clean, no borders
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setMinimumHeight(380)
        self.image_scroll_area.setMaximumHeight(420)  # Reduced slightly to give more room for telemetry
        self.image_scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.image_label = QLabel("Loading...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(520, 380)
        self.image_label.setStyleSheet("""
            QLabel {
                border: none;
                background-color: white;
                font-size: 14px;
                color: #6c757d;
            }
        """)
        
        self.image_scroll_area.setWidget(self.image_label)
        self.container_layout.addWidget(self.image_scroll_area)

        # Image info row - clean, no containers
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(10)
        
        # Image info
        self.image_info_label = QLabel("No image")
        self.image_info_label.setFont(QFont("Arial", 9))
        self.image_info_label.setWordWrap(True)
        self.image_info_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        
        # Download status
        self.download_progress_label = QLabel("Ready")
        self.download_progress_label.setFont(QFont("Arial", 9))
        self.download_progress_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        
        info_layout.addWidget(self.image_info_label, 2)
        info_layout.addWidget(self.download_progress_label, 1)
        
        self.container_layout.addLayout(info_layout)
        
        # Star Camera Telemetry Section - completely clean like GPS widget
        # Simple header with connection status
        telemetry_header_layout = QHBoxLayout()
        telemetry_header_layout.setContentsMargins(5, 10, 5, 5)
        
        telemetry_title = QLabel("Star Camera Telemetry")
        telemetry_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        telemetry_title.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
        
        # Connection status inline with title
        self.telemetry_connection_label = QLabel("Telemetry: Disconnected")
        self.telemetry_connection_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.telemetry_connection_label.setStyleSheet("QLabel { color: red; border: none; background: transparent; }")
        
        telemetry_header_layout.addWidget(telemetry_title)
        telemetry_header_layout.addStretch()
        telemetry_header_layout.addWidget(self.telemetry_connection_label)
        
        self.container_layout.addLayout(telemetry_header_layout)
        
        # Status indicators row - clean styling
        status_indicators_layout = QHBoxLayout()
        status_indicators_layout.setSpacing(15)
        status_indicators_layout.setContentsMargins(5, 0, 5, 5)
        
        # Auto focus status indicator
        self.auto_focus_status = QLabel("Focus: Idle")
        self.auto_focus_status.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.auto_focus_status.setStyleSheet("QLabel { color: #666666; padding: 2px 6px; background-color: #f0f0f0; border-radius: 3px; }")
        
        # Solving status indicator
        self.solving_status = QLabel("Solve: Idle")
        self.solving_status.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.solving_status.setStyleSheet("QLabel { color: #666666; padding: 2px 6px; background-color: #f0f0f0; border-radius: 3px; }")
        
        # Saving status indicator
        self.saving_status = QLabel("Save: Idle")
        self.saving_status.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.saving_status.setStyleSheet("QLabel { color: #666666; padding: 2px 6px; background-color: #f0f0f0; border-radius: 3px; }")
        
        status_indicators_layout.addWidget(self.auto_focus_status)
        status_indicators_layout.addWidget(self.solving_status)
        status_indicators_layout.addWidget(self.saving_status)
        status_indicators_layout.addStretch()
        
        self.container_layout.addLayout(status_indicators_layout)
        
        # Clean telemetry data grid - completely borderless like GPS widget
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)  # Clean spacing
        grid_layout.setContentsMargins(5, 5, 5, 10)
        
        self.telemetry_labels = {}
        
        # Reorganized telemetry fields in logical 2-column layout (4 columns total with labels)
        if self.current_telemetry.sc_focus_mode == 1:
            telemetry_fields = [
                # Row 1: Position coordinates
                ('start', 'Auto-focus start', '', 0, 0),
                ('stop', 'Auto-focus stop', '', 0, 2),
                # Row 2: Local coordinates  
                ('step', 'Auto-focus step', '', 1, 0),
                ('curr', 'Focus position', '', 1, 2),
                # Row 3: Camera settings
                ('exp', 'Exposure', 's', 2, 0),
            ]
        else:
            telemetry_fields = [
                # Row 1: Position coordinates
                ('ra', 'RA', '°', 0, 0),
                ('dec', 'DEC', '°', 0, 2),
                # Row 2: Local coordinates  
                ('az', 'Azimuth', '°', 1, 0),
                ('el', 'Elevation', '°', 1, 2),
                # Row 3: Camera settings
                ('exp', 'Exposure', 's', 2, 0),
                ('curr', 'Focus position','',2,2),
                ('fr', 'Field Rotation', '°', 3, 0),
                # Row 4: Additional rotation
                ('ir', 'Image Rotation', '°', 3, 2)
            ]
        
        for field, label_text, unit, row, col in telemetry_fields:
            # Create label with clean typography
            label = QLabel(f"{label_text}:")
            label.setFont(QFont("Arial", 9))
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            label.setWordWrap(True)  # Enable word wrapping
            label.setMaximumWidth(80)  # Reasonable width for telemetry labels
            
            # Create value label with clean, no-border style
            value_label = QLabel(f"N/A {unit}".strip())
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
            value_label.setMinimumWidth(80)
            
            # Add to layout
            grid_layout.addWidget(label, row, col)
            grid_layout.addWidget(value_label, row, col + 1)
            
            self.telemetry_labels[field] = value_label
        
        self.container_layout.addLayout(grid_layout)
        
        # Hidden labels that are referenced in other methods - keep them but invisible
        self.bandwidth_label = QLabel("Bandwidth: Unknown")
        self.bandwidth_label.setVisible(False)
        self.container_layout.addWidget(self.bandwidth_label)
        
        self.queue_label = QLabel("Queue: Unknown") 
        self.queue_label.setVisible(False)
        self.container_layout.addWidget(self.queue_label)
        
        self.next_update_label = QLabel("Next update: Soon")
        self.next_update_label.setVisible(False)
        self.container_layout.addWidget(self.next_update_label)
    
    def start_update_timers(self):
        """Start the update timers"""
        # Image update timer - every 10 seconds
        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.request_image)
        self.image_timer.start(int(STAR_CAMERA['update_interval'] * 1000))
        
        # Status update timer - every 5 seconds
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.request_status)
        self.status_timer.start(5000)
        
        # Telemetry update timer - every 1 second
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(1000)
        
        # Immediate first requests
        self.request_status()
        self.request_image()
        self.update_telemetry()
        
    def stop_update_timers(self):
        """Stop the update timers"""
        if hasattr(self, 'image_timer'):
            self.image_timer.stop()
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        if hasattr(self, 'telemetry_timer'):
            self.telemetry_timer.stop()
    
    def request_image(self):
        """Request latest image from server"""
        if self.is_active:
            self.download_progress_label.setText("Download: Requesting image...")
            self.trigger_fetch_image_signal.emit()
            
    def request_status(self):
        """Request server status"""
        if self.is_active:
            self.trigger_fetch_status_signal.emit()
    
    def update_telemetry(self):
        """Update telemetry display with current data"""
        if not self.is_active:
            return
            
        # Get current telemetry data
        self.current_telemetry = self.oph_client.get_data()
        
        # Update connection status
        if self.oph_client.is_connected():
            self.telemetry_connection_label.setText("Telemetry: Connected")
            self.telemetry_connection_label.setStyleSheet("QLabel { color: green; }")
        else:
            self.telemetry_connection_label.setText("Telemetry: Disconnected")
            self.telemetry_connection_label.setStyleSheet("QLabel { color: red; }")
        
        # Update status indicators
        if self.current_telemetry.valid:
            # Auto focus status
            if self.current_telemetry.sc_focus_mode == 1:
                if self.prev_focus_status == 0:
                    self.setup_active_display()
                    self.prev_focus_status = 1
                self.auto_focus_status.setText("Focus: AUTO FOCUSING")
                self.auto_focus_status.setStyleSheet("QLabel { color: white; padding: 2px 6px; background-color: orange; border-radius: 3px; font-weight: bold; }")
            else:
                if self.prev_focus_status == 1:
                    self.setup_active_display()
                    self.prev_focus_status = 0
                self.auto_focus_status.setText("Focus: Idle")
                self.auto_focus_status.setStyleSheet("QLabel { color: #666666; padding: 2px 6px; background-color: #f0f0f0; border-radius: 3px; }")
            
            # Solving status
            if self.current_telemetry.sc_solve == 1:
                self.solving_status.setText("Solve: SOLVING")
                self.solving_status.setStyleSheet("QLabel { color: white; padding: 2px 6px; background-color: blue; border-radius: 3px; font-weight: bold; }")
            else:
                self.solving_status.setText("Solve: Idle")
                self.solving_status.setStyleSheet("QLabel { color: #666666; padding: 2px 6px; background-color: #f0f0f0; border-radius: 3px; }")
                
            # Saving status
            if self.current_telemetry.sc_save == 1:
                self.saving_status.setText("Save: SAVING")
                self.saving_status.setStyleSheet("QLabel { color: white; padding: 2px 6px; background-color: blue; border-radius: 3px; font-weight: bold; }")
            else:
                self.saving_status.setText("Save: Idle")
                self.saving_status.setStyleSheet("QLabel { color: #666666; padding: 2px 6px; background-color: #f0f0f0; border-radius: 3px; }")
            
            
            # Update telemetry values
            if self.current_telemetry.sc_focus_mode == 1:
                telemetry_data = {
                    'start': (self.current_telemetry.sc_start_focus, '', 2),
                    'stop': (self.current_telemetry.sc_end_focus, '', 2),
                    'step': (self.current_telemetry.sc_focus_step, '', 2),
                    'curr': (self.current_telemetry.sc_curr_focus, '', 2),  # Using sc_alt for elevation
                    'exp': (self.current_telemetry.sc_texp, 's', 3)
                }
            else:
                telemetry_data = {
                    'ra': (self.current_telemetry.sc_ra, '°', 2),
                    'dec': (self.current_telemetry.sc_dec, '°', 2),
                    'az': (self.current_telemetry.sc_az, '°', 2),
                    'el': (self.current_telemetry.sc_alt, '°', 2),  # Using sc_alt for elevation
                    'exp': (self.current_telemetry.sc_texp, 's', 3),
                    'curr': (self.current_telemetry.sc_curr_focus,'',0),
                    'fr': (self.current_telemetry.sc_fr, '°', 2),
                    'ir': (self.current_telemetry.sc_ir, '°', 2)
                }
            
            for field, (value, unit, decimals) in telemetry_data.items():
                if field in self.telemetry_labels:
                    if decimals > 0:
                        formatted_value = f"{value:.{decimals}f} {unit}".strip()
                    else:
                        formatted_value = f"{int(value)} {unit}".strip()
                    self.telemetry_labels[field].setText(formatted_value)
                    self.telemetry_labels[field].setStyleSheet("QLabel { color: #212529; border: none; background: transparent; font-weight: bold; }")
        else:
            # Reset status indicators to disconnected state
            self.auto_focus_status.setText("Focus: N/A")
            self.auto_focus_status.setStyleSheet("QLabel { color: #999999; padding: 2px 6px; background-color: #e0e0e0; border-radius: 3px; }")
            self.solving_status.setText("Solve: N/A")
            self.solving_status.setStyleSheet("QLabel { color: #999999; padding: 2px 6px; background-color: #e0e0e0; border-radius: 3px; }")
            self.saving_status.setText("Save: N/A")
            self.saving_status.setStyleSheet("QLabel { color: #999999; padding: 2px 6px; background-color: #e0e0e0; border-radius: 3px; }")
            
            # Clear telemetry values
            for field, label in self.telemetry_labels.items():
                if field == 'exp':
                    label.setText("N/A s")
                else:
                    label.setText("N/A °")
                label.setStyleSheet("QLabel { color: #212529; border: none; background: transparent; }")
    
    def handle_image_update(self, new_image):
        """Update image display with new data"""
        if not self.is_active:
            return
            
        if new_image and new_image.valid and len(new_image.image_data) > 0:
            self.current_image = new_image
            self.last_fetch_time = dt.datetime.now()
            
            # Update rate calculation
            self.update_times.append(self.last_fetch_time)
            
            # Update display
            self.display_image(new_image)
            self.update_info_labels()
            self.download_progress_label.setText("Download: Complete")
            
        else:
            # Handle case where no image is available
            if new_image and not new_image.valid:
                self.download_progress_label.setText("Download: No images available on server")
                self.image_label.setText("No images available\n\nThe star camera server may not have\ncaptured any images yet.")
            else:
                self.download_progress_label.setText("Download: Failed")
                self.image_label.setText("Download failed\n\nCheck server connection and\nlog files for details.")
                
            self.update_info_labels(failed=True)
    
    def handle_status_update(self, status):
        """Update status display"""
        if not self.is_active:
            return
            
        self.current_status = status
        self.update_status_labels()
    
    def display_image(self, star_image: StarCameraImage):
        """Display the star camera image - RAW, no processing"""
        try:
            self.logger.info(f"Displaying raw image: {len(star_image.image_data)} bytes, {star_image.width}x{star_image.height}")
            
            # Convert image data to PIL Image - NO PROCESSING
            pil_image = Image.open(io.BytesIO(star_image.image_data))
            self.logger.info(f"PIL image opened: mode={pil_image.mode}, size={pil_image.size}")
            
            # Convert PIL image to bytes and load as QPixmap directly - NO ENHANCEMENT
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Load as QPixmap directly
            pixmap = QPixmap()
            if pixmap.loadFromData(img_buffer.getvalue()):
                self.logger.info(f"QPixmap loaded: {pixmap.width()}x{pixmap.height()}")
                
                # Scale to fit display area
                scaled_pixmap = pixmap.scaled(
                    510, 420, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Display the raw image
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("")
                self.download_progress_label.setText("Download: Complete")
                self.logger.info("Raw image display successful")
                
            else:
                self.logger.error("Failed to load image as QPixmap")
                self.image_label.setText("Error: Failed to load image")
                self.download_progress_label.setText("Download: Display error")
            
        except Exception as e:
            self.logger.error(f"Error displaying image: {e}", exc_info=True)
            self.image_label.setText(f"Error displaying image: {str(e)}")
            self.download_progress_label.setText("Download: Display error")
    
    def update_info_labels(self, failed=False):
        """Update image information labels"""
        if failed or not self.current_image or not self.current_image.valid:
            self.image_info_label.setText("No valid image")
        else:
            # Format image info
            timestamp = dt.datetime.fromtimestamp(self.current_image.timestamp)
            size_kb = self.current_image.total_size / 1024.0
            
            info_text = (f"Image: {self.current_image.width}x{self.current_image.height}, "
                        f"{size_kb:.1f} KB, Q{self.current_image.compression_quality}, "
                        f"{self.current_image.blob_count} stars")
            self.image_info_label.setText(info_text)
        
        # Update next update time
        if self.last_fetch_time:
            next_update = self.last_fetch_time + dt.timedelta(seconds=STAR_CAMERA['update_interval'])
            remaining = (next_update - dt.datetime.now()).total_seconds()
            if remaining > 0:
                self.next_update_label.setText(f"Next update: {remaining:.0f}s")
            else:
                self.next_update_label.setText("Next update: Soon")
        else:
            self.next_update_label.setText("Next update: Soon")
    
    def update_status_labels(self):
        """Update status information labels"""
        if not self.current_status or not self.current_status.valid:
            self.connection_status_label.setText("Status: Disconnected")
            self.connection_status_label.setStyleSheet("QLabel { color: red; }")
            self.bandwidth_label.setText("Bandwidth: Unknown")
            self.queue_label.setText("Queue: Unknown")
            self.download_progress_label.setText("Download: Server disconnected")
        else:
            # Connected and getting status
            self.connection_status_label.setText("Status: Connected")
            self.connection_status_label.setStyleSheet("QLabel { color: green; }")
            
            # Show bandwidth and queue info
            bandwidth_text = f"Bandwidth: {self.current_status.bandwidth_kbps} kbps"
            queue_text = f"Queue: {self.current_status.queue_size} images"
            self.bandwidth_label.setText(bandwidth_text)
            self.queue_label.setText(queue_text)
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate from client"""
        return self.star_camera_client.get_data_rate_kbps()
    
    def is_star_camera_active(self) -> bool:
        """Return whether star camera is currently active"""
        return self.is_active
    
    def is_connected(self) -> bool:
        """Return whether connected to server"""
        return self.current_status and self.current_status.valid
    
    def get_current_telemetry(self) -> OphData:
        """Get current telemetry data"""
        return self.current_telemetry if hasattr(self, 'current_telemetry') else OphData() 

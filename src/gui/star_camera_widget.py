"""
Star Camera Display Widget for BVEX Ground Station
Displays images from the star camera downlink server
"""

import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QPixmap, QImage
from PIL import Image
import datetime as dt
from collections import deque
import logging
import io

from src.data.star_camera_client import StarCameraClient, StarCameraImage
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

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        # Initialize star camera client (will be used in worker thread)
        self.star_camera_client = StarCameraClient()
        
        # Control state
        self.is_active = False
        
        # Data storage
        self.current_image = None
        self.current_status = None
        self.last_fetch_time = None
        
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
        self.setMinimumSize(400, 500)
        
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
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Top info bar - more compact
        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)
        
        self.connection_status_label = QLabel("Status: Connecting...")
        self.connection_status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.server_info_label = QLabel("Server: 100.85.84.122:8001")
        self.server_info_label.setFont(QFont("Arial", 10))  # Increased font size
        self.server_info_label.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        
        info_layout.addWidget(self.connection_status_label)
        info_layout.addStretch()
        info_layout.addWidget(self.server_info_label)
        
        self.container_layout.addWidget(info_frame)
        
        # Main content area - horizontal layout
        content_frame = QFrame()
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(15)
        
        # Left side - Image display (no extra frame/border)
        image_layout = QVBoxLayout()
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setMinimumHeight(300)  # Increased from 250 to 300
        self.image_scroll_area.setMaximumHeight(420)  # Increased from 350 to 420
        
        self.image_label = QLabel("Loading...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)  # Increased from 250 to 300
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #dee2e6;
                background-color: white;
                font-size: 14px;
                color: #6c757d;
            }
        """)
        
        self.image_scroll_area.setWidget(self.image_label)
        image_layout.addWidget(self.image_scroll_area)
        
        # Right side - Status and info (simple layout, no extra frame)
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(15, 0, 0, 0)  # Add left margin for spacing
        status_layout.setSpacing(12)
        
        # Image info (with border)
        image_info_group = QFrame()
        image_info_group.setFrameStyle(QFrame.Shape.StyledPanel)
        image_info_group.setStyleSheet("QFrame { border: 1px solid #dee2e6; background-color: #f8f9fa; padding: 8px; }")
        image_info_layout = QVBoxLayout(image_info_group)
        image_info_layout.setContentsMargins(8, 8, 8, 8)
        image_info_layout.setSpacing(4)
        
        image_info_title = QLabel("Image Info")
        image_info_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Increased from 10 to 12
        image_info_title.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        image_info_layout.addWidget(image_info_title)
        
        self.image_info_label = QLabel("No image")
        self.image_info_label.setFont(QFont("Arial", 11))  # Increased font size again
        self.image_info_label.setWordWrap(True)
        self.image_info_label.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        image_info_layout.addWidget(self.image_info_label)
        
        self.next_update_label = QLabel("Next update: Soon")
        self.next_update_label.setFont(QFont("Arial", 11))  # Increased font size
        self.next_update_label.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        image_info_layout.addWidget(self.next_update_label)
        
        status_layout.addWidget(image_info_group)
        
        # Server status (no frame, just labels)
        server_status_title = QLabel("Server Status")
        server_status_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Increased from 10 to 12
        server_status_title.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        status_layout.addWidget(server_status_title)
        
        self.download_progress_label = QLabel("Download: Complete")
        self.download_progress_label.setFont(QFont("Arial", 11))  # Increased font size
        self.download_progress_label.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        status_layout.addWidget(self.download_progress_label)
        
        self.bandwidth_label = QLabel("Bandwidth: 0 kbps")
        self.bandwidth_label.setFont(QFont("Arial", 11))  # Increased font size
        self.bandwidth_label.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        status_layout.addWidget(self.bandwidth_label)
        
        self.queue_label = QLabel("Queue: 1 images")
        self.queue_label.setFont(QFont("Arial", 11))  # Increased font size
        self.queue_label.setStyleSheet("QLabel { color: #000000; }")  # Changed to black
        status_layout.addWidget(self.queue_label)
        
        status_layout.addStretch()  # Push everything to top
        
        # Add to content layout
        content_layout.addLayout(image_layout, 3)  # Image gets 3/4 of the space
        content_layout.addLayout(status_layout, 1)  # Status gets 1/4 of the space
        
        self.container_layout.addWidget(content_frame)
    
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
        
        # Immediate first requests
        self.request_status()
        self.request_image()
        
    def stop_update_timers(self):
        """Stop the update timers"""
        if hasattr(self, 'image_timer'):
            self.image_timer.stop()
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
    
    def request_image(self):
        """Request latest image from server"""
        if self.is_active:
            self.download_progress_label.setText("Download: Requesting image...")
            self.trigger_fetch_image_signal.emit()
            
    def request_status(self):
        """Request server status"""
        if self.is_active:
            self.trigger_fetch_status_signal.emit()
    
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
        """Display the star camera image"""
        try:
            # Convert image data to QPixmap
            pil_image = Image.open(io.BytesIO(star_image.image_data))
            
            # Convert PIL image to QImage
            if pil_image.mode == 'RGB':
                rgb_image = pil_image
            else:
                rgb_image = pil_image.convert('RGB')
                
            h, w, ch = np.array(rgb_image).shape
            bytes_per_line = ch * w
            qt_image = QImage(np.array(rgb_image).data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Scale image to fit the horizontal layout better
            pixmap = QPixmap.fromImage(qt_image)
            # Use dimensions that match the new more horizontal layout
            scaled_pixmap = pixmap.scaled(500, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")  # Clear text
            
            self.download_progress_label.setText("Download: Complete")
            
        except Exception as e:
            self.logger.error(f"Error displaying image: {e}")
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
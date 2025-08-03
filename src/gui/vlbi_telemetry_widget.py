"""
VLBI Telemetry Widget for BVEX Ground Station
Displays real-time VLBI status from Saggitarius server
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont
import datetime as dt
from collections import deque

from src.data.vlbi_client import VLBITelemetryClient, VLBIData



class VLBIWorker(QObject):
    """Worker to fetch VLBI data in a separate thread"""
    data_updated = pyqtSignal(object)
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    def fetch_data(self):
        """Fetch VLBI telemetry data"""
        success = self.client.update_data()
        self.data_updated.emit(self.client.current_data)


class VLBITelemetryWidget(QWidget):
    """Widget displaying real-time VLBI telemetry data"""
    trigger_fetch_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize VLBI client
        self.vlbi_client = VLBITelemetryClient()
        
        # Control state
        self.is_active = False
        
        # Data storage
        self.current_data = VLBIData()
        self.last_fetch_time = 0
        
        # History for data rate calculation
        self.update_times = deque(maxlen=10)
        
        self.setup_ui()
        self.setup_worker_thread()
        
        self.logger.info("VLBI Telemetry Widget initialized (OFF by default)")
    
    def setup_worker_thread(self):
        """Setup the worker thread for non-blocking data fetching"""
        self.worker_thread = QThread()
        self.worker = VLBIWorker(self.vlbi_client)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker.data_updated.connect(self.handle_data_update)
        self.trigger_fetch_signal.connect(self.worker.fetch_data)
        
        self.worker_thread.start()
    
    def setup_ui(self):
        """Initialize the clean user interface matching GPS/Motor Controller style"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("VLBI Monitor: OFF")
        self.control_status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.control_status_label.setStyleSheet("QLabel { color: red; }")
        
        # Frequency dropdown
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["1 Hz", "5 Hz", "10 Hz"])
        self.frequency_combo.setCurrentText("5 Hz")
        self.frequency_combo.setMinimumWidth(80)
        self.frequency_combo.setMaximumWidth(100)
        self.frequency_combo.currentTextChanged.connect(self.on_frequency_changed)
        self.frequency_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
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
        self.setMinimumWidth(380)
        self.setMaximumWidth(450)
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add centered message
        message_label = QLabel("VLBI Monitor - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start VLBI monitoring')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 12))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active VLBI display with all data fields"""
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
        """Create clean VLBI connection status header"""
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
        
        # VLBI Connected text
        self.status_label = QLabel("VLBI Connected")
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: black; }")
        
        # Status indicator dot
        self.status_dot = QLabel("●")
        dot_font = QFont()
        dot_font.setPointSize(16)
        self.status_dot.setFont(dot_font)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_dot.setStyleSheet("QLabel { color: black; }")
        
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addSpacing(8)
        layout.addWidget(self.status_dot)
        layout.addStretch()
        
        # Initialize as disconnected
        self._update_status_display(False)
        
        return header
    
    def _create_data_section(self):
        """Create clean data section with VLBI status information"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Main layout for data
        main_layout = QVBoxLayout(data_frame)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status section
        status_section = self._create_status_section()
        main_layout.addWidget(status_section)
        
        # Statistics section
        stats_section = self._create_statistics_section()
        main_layout.addWidget(stats_section)
        
        return data_frame
    
    def _create_status_section(self):
        """Create VLBI status section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QGridLayout(section)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("Status")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(title, 0, 0, 1, 3)
        
        # Running status
        running_label_text = QLabel("Running:")
        running_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(running_label_text, 1, 0)
        self.running_label = QLabel("Unknown")
        self.running_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.running_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.running_label, 1, 1)
        
        # Stage
        stage_label_text = QLabel("Stage:")
        stage_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(stage_label_text, 1, 2)
        self.stage_label = QLabel("Unknown")
        self.stage_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.stage_label, 1, 3)
        
        # Connection
        connection_label_text = QLabel("Connection:")
        connection_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(connection_label_text, 2, 0)
        self.connection_label = QLabel("Unknown")
        self.connection_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connection_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.connection_label, 2, 1)
        
        # Errors
        errors_label_text = QLabel("Errors:")
        errors_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(errors_label_text, 2, 2)
        self.errors_label = QLabel("0")
        self.errors_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.errors_label, 2, 3)
        
        return section
    
    def _create_statistics_section(self):
        """Create VLBI statistics section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QGridLayout(section)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("Statistics")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(title, 0, 0, 1, 3)
        
        # Packets
        packets_label_text = QLabel("Packets:")
        packets_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(packets_label_text, 1, 0)
        self.packets_label = QLabel("0")
        self.packets_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.packets_label, 1, 1)
        
        # Data volume
        data_label_text = QLabel("Data:")
        data_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(data_label_text, 1, 2)
        self.data_volume_label = QLabel("0.0 MB")
        self.data_volume_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.data_volume_label, 1, 3)
        
        # Update rate
        rate_label_text = QLabel("Rate:")
        rate_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(rate_label_text, 2, 0)
        self.update_rate_label = QLabel("0.0 Hz")
        self.update_rate_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.update_rate_label, 2, 1)
        
        # Last update
        updated_label_text = QLabel("Updated:")
        updated_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(updated_label_text, 2, 2)
        self.last_update_label = QLabel("Never")
        self.last_update_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.last_update_label, 2, 3)
        
        return section
    
    def _update_status_display(self, connected):
        """Update the status header display"""
        if not hasattr(self, 'status_label') or not hasattr(self, 'status_dot'):
            return
            
        if connected:
            self.status_label.setText("VLBI Connected")
            self.status_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")  # Dark green - visible
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("QLabel { color: #006400; }")  # Dark green - visible
        else:
            self.status_label.setText("VLBI Disconnected")
            self.status_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")  # Dark red - visible
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("QLabel { color: #8b0000; }")  # Dark red - visible
    
    def toggle_state(self):
        """Toggle VLBI monitoring on/off"""
        if self.is_active:
            self.stop_vlbi()
        else:
            self.start_vlbi()
    
    def start_vlbi(self):
        """Start VLBI telemetry monitoring"""
        if self.is_active:
            return
        
        self.is_active = True
        
        # Update control UI
        self.control_status_label.setText("VLBI Monitor: ON")
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
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.trigger_fetch)
        frequency = int(self.frequency_combo.currentText().split()[0])
        self.update_timer.start(1000 // frequency)  # Convert Hz to ms
        
        self.logger.info("VLBI telemetry monitoring started")
    
    def stop_vlbi(self):
        """Stop VLBI telemetry monitoring"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Stop timer
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Update control UI
        self.control_status_label.setText("VLBI Monitor: OFF")
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
        
        # Show static display
        self.setup_static_display()
        
        self.logger.info("VLBI telemetry monitoring stopped")
    
    def trigger_fetch(self):
        """Trigger a data fetch"""
        if not self.is_active:
            return
        
        current_time = dt.datetime.now().timestamp()
        if current_time - self.last_fetch_time > 0.5:  # 0.5 second cooldown
            self.last_fetch_time = current_time
            self.trigger_fetch_signal.emit()
    
    def handle_data_update(self, data):
        """Handle updated VLBI data"""
        self.current_data = data
        self.update_display()
        
        # Track update rate
        self.update_times.append(dt.datetime.now())
    
    def update_display(self):
        """Update the display with current VLBI data"""
        if not self.current_data.valid:
            self.update_display_error()
            return
        
        # Update status header
        connected = self.current_data.valid and self.vlbi_client.is_connected()
        self._update_status_display(connected)
        
        # Handle "not available" case
        if self.current_data.stage == "not_available":
            self.running_label.setText("NOT AVAILABLE")
            self.running_label.setStyleSheet("QLabel { color: #ff8c00; font-weight: bold; }")  # Dark orange - visible
            
            self.stage_label.setText("VLBI Not Running")
            self.stage_label.setStyleSheet("QLabel { color: black; }")
            
            self.connection_label.setText("Server Connected")
            self.connection_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")  # Dark green - visible
        else:
            # Update running status
            if self.current_data.running:
                self.running_label.setText("ACTIVE")
                self.running_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")  # Dark green - visible
            else:
                self.running_label.setText("STOPPED")
                self.running_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")  # Dark red - visible
            
            # Update stage
            self.stage_label.setText(self.current_data.stage.title())
            self.stage_label.setStyleSheet("QLabel { color: black; }")
            
            # Update connection status
            if self.current_data.connection in ["connected", "capturing"]:
                self.connection_label.setText(self.current_data.connection.title())
                self.connection_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")  # Dark green - visible
            elif self.current_data.connection == "disconnected":
                self.connection_label.setText("Disconnected")
                self.connection_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")  # Dark red - visible
            else:
                self.connection_label.setText(self.current_data.connection.title())
                self.connection_label.setStyleSheet("QLabel { color: #ff8c00; font-weight: bold; }")  # Dark orange - visible
        
        # Update error count
        if self.current_data.errors > 0:
            self.errors_label.setText(f"{self.current_data.errors}")
            self.errors_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")  # Dark red - visible
        else:
            self.errors_label.setText("0")
            self.errors_label.setStyleSheet("QLabel { color: #006400; }")  # Dark green - visible
        
        # Update statistics
        self.packets_label.setText(f"{self.current_data.packets:,}")
        self.data_volume_label.setText(f"{self.current_data.data_mb:.1f} MB")
        
        # Update timestamps
        if self.current_data.last_update:
            try:
                # Parse timestamp and show relative time
                from datetime import datetime
                timestamp = datetime.fromisoformat(self.current_data.last_update.replace('Z', '+00:00'))
                time_diff = datetime.now() - timestamp.replace(tzinfo=None)
                if time_diff.total_seconds() < 60:
                    self.last_update_label.setText("Just now")
                else:
                    minutes_ago = int(time_diff.total_seconds() // 60)
                    self.last_update_label.setText(f"{minutes_ago}m ago")
            except:
                self.last_update_label.setText("Recently")
        else:
            self.last_update_label.setText("Unknown")
        
        # Calculate and display update rate
        self.calculate_update_rate()
    
    def update_display_error(self):
        """Update display when there's an error or no data"""
        # Update status header
        self._update_status_display(False)
        
        # Set all data to unknown/error with visible colors
        self.running_label.setText("Unknown")
        self.running_label.setStyleSheet("QLabel { color: #666666; }")  # Dark gray - visible
        
        self.connection_label.setText("Unknown")
        self.connection_label.setStyleSheet("QLabel { color: #666666; }")  # Dark gray - visible
        
        self.stage_label.setText("Unknown")
        self.stage_label.setStyleSheet("QLabel { color: black; }")
        self.errors_label.setText("N/A")
        self.errors_label.setStyleSheet("QLabel { color: black; }")
        self.packets_label.setText("N/A")
        self.packets_label.setStyleSheet("QLabel { color: black; }")
        self.data_volume_label.setText("N/A")
        self.data_volume_label.setStyleSheet("QLabel { color: black; }")
        self.last_update_label.setText("Error")
        self.last_update_label.setStyleSheet("QLabel { color: black; }")
        self.update_rate_label.setText("0.0 Hz")
        self.update_rate_label.setStyleSheet("QLabel { color: black; }")
    
    def calculate_update_rate(self):
        """Calculate and display current update rate"""
        if len(self.update_times) < 2:
            self.update_rate_label.setText("0.0 Hz")
            return
        
        # Calculate rate from recent updates
        now = dt.datetime.now()
        recent_updates = [t for t in self.update_times if (now - t).total_seconds() < 10]
        
        if len(recent_updates) >= 2:
            time_span = (recent_updates[-1] - recent_updates[0]).total_seconds()
            if time_span > 0:
                rate = (len(recent_updates) - 1) / time_span
                self.update_rate_label.setText(f"{rate:.1f} Hz")
            else:
                self.update_rate_label.setText("0.0 Hz")
        else:
            self.update_rate_label.setText("0.0 Hz")
    
    def on_frequency_changed(self):
        """Handle frequency change"""
        if self.is_active:
            # Restart timer with new frequency
            self.update_timer.stop()
            frequency = int(self.frequency_combo.currentText().split()[0])
            self.update_timer.start(1000 // frequency)
            self.logger.info(f"VLBI update frequency changed to {frequency} Hz")
    
    def is_vlbi_active(self) -> bool:
        """Check if VLBI monitoring is active"""
        return self.is_active
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate in KB/s"""
        return self.vlbi_client.get_data_rate_kbps()
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop_vlbi()
        
        # Stop worker thread
        if hasattr(self, 'worker_thread'):
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Clean up client
        if hasattr(self, 'vlbi_client'):
            self.vlbi_client.cleanup()
        
        # Clear data
        self.update_times.clear()
        
        self.logger.info("VLBI telemetry widget cleaned up")
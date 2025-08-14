"""
Backend Computer Status Widget for BVEX Ground Station
Displays real-time Aquila backend system status including CPU temperature and SSD usage
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont
import datetime as dt
from collections import deque

from src.data.aquila_client import AquilaClient, AquilaData


class AquilaWorker(QObject):
    """Worker to fetch Aquila backend data in a separate thread"""
    data_updated = pyqtSignal(object)
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    def fetch_data(self):
        """Fetch Aquila backend data"""
        success = self.client.update_data()
        self.data_updated.emit(self.client.current_data)


class BackendStatusWidget(QWidget):
    """Widget displaying real-time Aquila backend computer status"""
    trigger_fetch_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize Aquila client
        self.aquila_client = AquilaClient()
        
        # Control state
        self.is_active = False
        
        # Data storage
        self.current_data = AquilaData()
        self.last_fetch_time = 0
        
        # History for data rate calculation
        self.update_times = deque(maxlen=10)
        
        self.setup_ui()
        self.setup_worker_thread()
        
        self.logger.info("Backend Status Widget initialized (OFF by default)")
    
    def setup_worker_thread(self):
        """Setup the worker thread for non-blocking data fetching"""
        self.worker_thread = QThread()
        self.worker = AquilaWorker(self.aquila_client)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker.data_updated.connect(self.handle_data_update)
        self.trigger_fetch_signal.connect(self.worker.fetch_data)
        
        self.worker_thread.start()
    
    def setup_ui(self):
        """Initialize the clean user interface matching VLBI/TICC style"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Backend Monitor: OFF")
        self.control_status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.control_status_label.setStyleSheet("QLabel { color: red; }")
        
        # Frequency dropdown
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["1 Hz", "2 Hz", "5 Hz"])
        self.frequency_combo.setCurrentText("2 Hz")  # Default to 2Hz for system monitoring
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
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        self.setMinimumHeight(300)
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add centered message
        message_label = QLabel("Backend Monitor - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start backend monitoring')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 12))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active backend status display with all data fields"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # CPU section
        cpu_section = self._create_cpu_section()
        self.container_layout.addWidget(cpu_section)
        
        # Storage section
        storage_section = self._create_storage_section()
        self.container_layout.addWidget(storage_section)
        
        # Statistics section
        stats_section = self._create_statistics_section()
        self.container_layout.addWidget(stats_section)
    
    def _create_status_header(self):
        """Create clean backend connection status header"""
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
        
        # Backend Connected text
        self.status_label = QLabel("Backend Connected")
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
    
    def _create_cpu_section(self):
        """Create CPU temperature section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QGridLayout(section)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("CPU Temperature")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(title, 0, 0, 1, 3)
        
        # CPU temperature
        temp_label_text = QLabel("Temperature:")
        temp_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(temp_label_text, 1, 0)
        
        self.cpu_temp_label = QLabel("--°C")
        self.cpu_temp_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.cpu_temp_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.cpu_temp_label, 1, 1)
        
        # Memory usage
        memory_label_text = QLabel("Memory:")
        memory_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(memory_label_text, 1, 2)
        
        self.memory_label = QLabel("--%")
        self.memory_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.memory_label, 1, 3)
        
        return section
    
    def _create_storage_section(self):
        """Create storage (SSD) status section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QGridLayout(section)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section title
        title = QLabel("NVMe Storage")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(title, 0, 0, 1, 4)
        
        # SSD1
        ssd1_label = QLabel("SSD1:")
        ssd1_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        ssd1_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(ssd1_label, 1, 0)
        
        self.ssd1_status_label = QLabel("Unknown")
        self.ssd1_status_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.ssd1_status_label, 1, 1)
        
        self.ssd1_progress = QProgressBar()
        self.ssd1_progress.setMinimumWidth(100)
        self.ssd1_progress.setMaximumHeight(20)
        self.ssd1_progress.setTextVisible(True)
        layout.addWidget(self.ssd1_progress, 1, 2)
        
        self.ssd1_space_label = QLabel("-- GB")
        self.ssd1_space_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.ssd1_space_label, 1, 3)
        
        # SSD2
        ssd2_label = QLabel("SSD2:")
        ssd2_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        ssd2_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(ssd2_label, 2, 0)
        
        self.ssd2_status_label = QLabel("Unknown")
        self.ssd2_status_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.ssd2_status_label, 2, 1)
        
        self.ssd2_progress = QProgressBar()
        self.ssd2_progress.setMinimumWidth(100)
        self.ssd2_progress.setMaximumHeight(20)
        self.ssd2_progress.setTextVisible(True)
        layout.addWidget(self.ssd2_progress, 2, 2)
        
        self.ssd2_space_label = QLabel("-- GB")
        self.ssd2_space_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.ssd2_space_label, 2, 3)
        
        return section
    
    def _create_statistics_section(self):
        """Create statistics section"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QGridLayout(section)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Update rate
        rate_label_text = QLabel("Rate:")
        rate_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(rate_label_text, 0, 0)
        self.update_rate_label = QLabel("0.0 Hz")
        self.update_rate_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.update_rate_label, 0, 1)
        
        # Last update
        updated_label_text = QLabel("Updated:")
        updated_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(updated_label_text, 0, 2)
        self.last_update_label = QLabel("Never")
        self.last_update_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.last_update_label, 0, 3)
        
        return section
    
    def _update_status_display(self, connected):
        """Update the status header display"""
        # Check if widgets exist and haven't been deleted
        status_label = getattr(self, 'status_label', None)
        status_dot = getattr(self, 'status_dot', None)
        
        if not status_label or not status_dot:
            return
            
        try:
            if connected:
                status_label.setText("Backend Connected")
                status_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")  # Dark green
                status_dot.setText("●")
                status_dot.setStyleSheet("QLabel { color: #006400; }")  # Dark green
            else:
                status_label.setText("Backend Disconnected")
                status_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")  # Dark red
                status_dot.setText("●")
                status_dot.setStyleSheet("QLabel { color: #8b0000; }")  # Dark red
        except RuntimeError:
            # Widget has been deleted, stop trying to update it
            pass
    
    def toggle_state(self):
        """Toggle backend monitoring on/off"""
        if self.is_active:
            self.stop_backend()
        else:
            self.start_backend()
    
    def start_backend(self):
        """Start backend telemetry monitoring"""
        if self.is_active:
            return
        
        self.is_active = True
        
        # Update control UI
        self.control_status_label.setText("Backend Monitor: ON")
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
        
        self.logger.info("Backend telemetry monitoring started")
    
    def stop_backend(self):
        """Stop backend telemetry monitoring"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Stop timer
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Update control UI
        self.control_status_label.setText("Backend Monitor: OFF")
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
        
        self.logger.info("Backend telemetry monitoring stopped")
    
    def trigger_fetch(self):
        """Trigger a data fetch"""
        if not self.is_active:
            return
        
        current_time = dt.datetime.now().timestamp()
        if current_time - self.last_fetch_time > 0.5:  # 0.5 second cooldown
            self.last_fetch_time = current_time
            self.trigger_fetch_signal.emit()
    
    def handle_data_update(self, data):
        """Handle updated backend data"""
        # Check if widget is still active and not being destroyed
        if not self.is_active or not hasattr(self, 'current_data'):
            return
            
        self.current_data = data
        
        # Only update display if widgets still exist
        try:
            self.update_display()
            # Track update rate
            self.update_times.append(dt.datetime.now())
        except RuntimeError as e:
            # Widget has been deleted - stop processing
            self.logger.debug(f"Widget deleted during update, stopping backend monitoring: {e}")
            self.is_active = False
    
    def update_display(self):
        """Update the display with current backend data"""
        # Check if widget is being destroyed
        if not hasattr(self, 'current_data') or not hasattr(self, 'cpu_temp_label'):
            return
            
        if not self.current_data.valid:
            self.update_display_error()
            return
        
        # Update status header
        connected = self.current_data.valid and self.aquila_client.is_connected()
        self._update_status_display(connected)
        
        # Update CPU temperature with color coding
        cpu_temp = self.current_data.cpu_temp
        
        # Check if widget still exists before updating
        if hasattr(self, 'cpu_temp_label') and self.cpu_temp_label:
            self.cpu_temp_label.setText(f"{cpu_temp:.1f}°C")
        
            # Color code CPU temperature
            if cpu_temp < 50:
                self.cpu_temp_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")  # Green: cool
            elif cpu_temp < 70:
                self.cpu_temp_label.setStyleSheet("QLabel { color: #ff8c00; font-weight: bold; }")  # Orange: warm
            else:
                self.cpu_temp_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")  # Red: hot
        
        # Update memory usage
        if hasattr(self, 'memory_label') and self.memory_label:
            self.memory_label.setText(f"{self.current_data.memory_percent:.1f}%")
        
        # Update SSD1
        self._update_ssd_display("ssd1")
        
        # Update SSD2
        self._update_ssd_display("ssd2")
        
        # Update statistics
        self.calculate_update_rate()
        
        # Update last update time
        if hasattr(self, 'last_update_label') and self.last_update_label:
            try:
                timestamp = dt.datetime.fromtimestamp(self.current_data.last_update_time)
                time_diff = dt.datetime.now() - timestamp
                if time_diff.total_seconds() < 60:
                    self.last_update_label.setText("Just now")
                else:
                    minutes_ago = int(time_diff.total_seconds() // 60)
                    self.last_update_label.setText(f"{minutes_ago}m ago")
            except:
                self.last_update_label.setText("Recently")
    
    def _update_ssd_display(self, ssd_name):
        """Update display for a specific SSD"""
        # Check if widget is being destroyed
        if not hasattr(self, 'current_data') or not self.current_data:
            return
            
        if ssd_name == "ssd1":
            mounted = self.current_data.ssd1_mounted
            percent = self.current_data.ssd1_percent
            used_gb = self.current_data.ssd1_used_gb
            total_gb = self.current_data.ssd1_total_gb
            status_label = getattr(self, 'ssd1_status_label', None)
            progress_bar = getattr(self, 'ssd1_progress', None)
            space_label = getattr(self, 'ssd1_space_label', None)
        else:  # ssd2
            mounted = self.current_data.ssd2_mounted
            percent = self.current_data.ssd2_percent
            used_gb = self.current_data.ssd2_used_gb
            total_gb = self.current_data.ssd2_total_gb
            status_label = getattr(self, 'ssd2_status_label', None)
            progress_bar = getattr(self, 'ssd2_progress', None)
            space_label = getattr(self, 'ssd2_space_label', None)
        
        # Skip update if widgets don't exist
        if not all([status_label, progress_bar, space_label]):
            return
        
        # Update mount status
        if mounted:
            status_label.setText("Mounted")
            status_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")  # Green
        else:
            status_label.setText("Unmounted")
            status_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")  # Red
        
        # Update progress bar
        if mounted and total_gb > 0:
            progress_bar.setValue(int(percent))
            progress_bar.setFormat(f"{percent:.1f}%")
            
            # Color code based on usage
            if percent < 80:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")  # Green
            elif percent < 90:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")  # Yellow
            else:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")  # Red
            
            # Update space label
            space_label.setText(f"{used_gb:.1f}/{total_gb:.1f} GB")
        else:
            progress_bar.setValue(0)
            progress_bar.setFormat("N/A")
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #6c757d; }")  # Gray
            space_label.setText("-- GB")
    
    def update_display_error(self):
        """Update display when there's an error or no data"""
        # Update status header
        self._update_status_display(False)
        
        # Set all data to unknown/error
        self.cpu_temp_label.setText("--°C")
        self.cpu_temp_label.setStyleSheet("QLabel { color: #666666; }")  # Gray
        
        self.memory_label.setText("--%")
        
        # Update SSDs
        for status_label, progress_bar, space_label in [
            (self.ssd1_status_label, self.ssd1_progress, self.ssd1_space_label),
            (self.ssd2_status_label, self.ssd2_progress, self.ssd2_space_label)
        ]:
            status_label.setText("Unknown")
            status_label.setStyleSheet("QLabel { color: #666666; }")  # Gray
            progress_bar.setValue(0)
            progress_bar.setFormat("N/A")
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #6c757d; }")  # Gray
            space_label.setText("-- GB")
        
        self.update_rate_label.setText("0.0 Hz")
        self.last_update_label.setText("Error")
    
    def calculate_update_rate(self):
        """Calculate and display current update rate"""
        # Check if widget exists
        update_rate_label = getattr(self, 'update_rate_label', None)
        if not update_rate_label or not hasattr(self, 'update_times'):
            return
            
        try:
            if len(self.update_times) < 2:
                update_rate_label.setText("0.0 Hz")
                return
            
            # Calculate rate from recent updates
            now = dt.datetime.now()
            recent_updates = [t for t in self.update_times if (now - t).total_seconds() < 10]
            
            if len(recent_updates) >= 2:
                time_span = (recent_updates[-1] - recent_updates[0]).total_seconds()
                if time_span > 0:
                    rate = (len(recent_updates) - 1) / time_span
                    update_rate_label.setText(f"{rate:.1f} Hz")
                else:
                    update_rate_label.setText("0.0 Hz")
            else:
                update_rate_label.setText("0.0 Hz")
        except RuntimeError:
            # Widget has been deleted
            pass
    
    def on_frequency_changed(self):
        """Handle frequency change"""
        if self.is_active:
            # Restart timer with new frequency
            self.update_timer.stop()
            frequency = int(self.frequency_combo.currentText().split()[0])
            self.update_timer.start(1000 // frequency)
            self.logger.info(f"Backend update frequency changed to {frequency} Hz")
    
    def is_backend_active(self) -> bool:
        """Check if backend monitoring is active"""
        return self.is_active
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate in KB/s"""
        return self.aquila_client.get_data_rate_kbps()
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        self.logger.info("Starting backend status widget cleanup...")
        
        # Stop backend monitoring first
        self.stop_backend()
        
        # Disconnect signals to prevent updates during cleanup
        try:
            if hasattr(self, 'trigger_fetch_signal'):
                self.trigger_fetch_signal.disconnect()
        except:
            pass
        
        # Stop worker thread gracefully
        if hasattr(self, 'worker_thread') and self.worker_thread:
            try:
                if hasattr(self, 'worker') and self.worker:
                    # Disconnect worker signals
                    try:
                        self.worker.data_updated.disconnect()
                    except:
                        pass
                
                # Quit and wait for thread
                self.worker_thread.quit()
                if not self.worker_thread.wait(3000):  # 3 second timeout
                    self.logger.warning("Worker thread did not terminate gracefully, forcing termination")
                    self.worker_thread.terminate()
                    self.worker_thread.wait(1000)  # Wait 1 more second
                    
                self.logger.debug("Worker thread terminated successfully")
            except Exception as e:
                self.logger.error(f"Error stopping worker thread: {e}")
        
        # Clean up client
        if hasattr(self, 'aquila_client'):
            try:
                self.aquila_client.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up aquila client: {e}")
        
        # Clear data structures
        try:
            if hasattr(self, 'update_times'):
                self.update_times.clear()
            if hasattr(self, 'current_data'):
                self.current_data = None
        except Exception as e:
            self.logger.error(f"Error clearing data structures: {e}")
        
        self.logger.info("Backend status widget cleanup completed")


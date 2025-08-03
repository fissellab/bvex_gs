"""
System Monitor Widget for BVEX Ground Station
Displays real-time system metrics from both Ophiuchus and Saggitarius flight computers
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QComboBox, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont
import datetime as dt
from collections import deque

from src.data.system_monitor_client import SystemMonitorClient, SystemData


class SystemMonitorWorker(QObject):
    """Worker to fetch system data in a separate thread"""
    data_updated = pyqtSignal(str, object)  # system_name, data
    
    def __init__(self, clients):
        super().__init__()
        self.clients = clients  # Dict of system_name -> client
    
    def fetch_data(self):
        """Fetch system data from all clients"""
        for system_name, client in self.clients.items():
            success = client.update_data()
            self.data_updated.emit(system_name, client.current_data)


class SystemMonitorWidget(QWidget):
    """Widget displaying real-time system monitoring data from both flight computers"""
    trigger_fetch_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize system monitor clients
        self.clients = {
            'ophiuchus': SystemMonitorClient('ophiuchus'),
            'saggitarius': SystemMonitorClient('saggitarius')
        }
        
        # Control state
        self.is_active = False
        
        # Data storage
        self.system_data = {
            'ophiuchus': SystemData(),
            'saggitarius': SystemData()
        }
        self.last_fetch_time = 0
        
        # History for data rate calculation
        self.update_times = deque(maxlen=10)
        
        self.setup_ui()
        self.setup_worker_thread()
        
        self.logger.info("System Monitor Widget initialized (OFF by default)")
    
    def setup_worker_thread(self):
        """Setup the worker thread for non-blocking data fetching"""
        self.worker_thread = QThread()
        self.worker = SystemMonitorWorker(self.clients)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker.data_updated.connect(self.handle_data_update)
        self.trigger_fetch_signal.connect(self.worker.fetch_data)
        
        self.worker_thread.start()
    
    def setup_ui(self):
        """Initialize the clean user interface matching PBoB widget style"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Main status label
        self.control_status_label = QLabel("System Monitor: OFF")
        self.control_status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.control_status_label.setStyleSheet("QLabel { color: red; }")
        
        # Data logging indicator
        self.logging_indicator_label = QLabel("")
        self.logging_indicator_label.setFont(QFont("Arial", 10))
        self.logging_indicator_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        
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
        control_layout.addWidget(self.logging_indicator_label)
        control_layout.addStretch()
        control_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(control_layout)
        
        # Create the main container with clean styling like PBoB widget
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
        
        # Set proper size - taller to prevent text cutoff
        self.setMinimumSize(650, 280)  # Increased height from 200 to 280
        self.setMaximumSize(750, 350)  # Increased height from 250 to 350
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        self.clear_widget(self.container_layout)
        
        # Add centered message
        message_label = QLabel("System Monitor - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start monitoring both flight computers')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 10))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def clear_widget(self, layout):
        """Clear all widgets from a layout (similar to PBoB widget)"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
            elif child.layout():
                self.clear_widget(child.layout())
    
    def setup_active_display(self):
        """Setup the active system monitor display with clean layout like PBoB widget"""
        # Clear existing widgets
        self.clear_widget(self.container_layout)
        
        # Status header like PBoB widget
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Main data section
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
    
    def _create_status_header(self):
        """Create clean status header like PBoB widget"""
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
        title_label = QLabel("Flight Computer Systems")
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
        """Create clean data section like GPS widget - side by side systems"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Use QGridLayout: 1 row, 3 columns (Ophiuchus | Separator | Saggitarius)
        main_layout = QGridLayout(data_frame)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Ophiuchus section (left side) - column 0
        oph_section = self._create_system_section("Ophiuchus")
        main_layout.addWidget(oph_section, 0, 0)
        
        # Vertical separator line - column 1
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #dee2e6; }")
        main_layout.addWidget(separator, 0, 1)
        
        # Saggitarius section (right side) - column 2
        sag_section = self._create_system_section("Saggitarius")
        main_layout.addWidget(sag_section, 0, 2)
        
        return data_frame
    
    def _create_system_section(self, system_name):
        """Create clean system section like GPS widget sections"""
        section = QFrame()
        section.setFrameStyle(QFrame.Shape.NoFrame)
        section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        layout = QVBoxLayout(section)
        layout.setSpacing(4)  # Increased from 2 to give more room
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Section header
        header = QLabel(system_name)
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: #495057;
                border: none;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 1px;
                margin-bottom: 2px;
            }
        """)
        layout.addWidget(header)
        
        # CPU Temperature
        cpu_layout = QVBoxLayout()
        cpu_layout.setSpacing(2)  # Increased from 1
        
        cpu_label = QLabel("CPU Temp:")
        cpu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cpu_label_font = QFont()
        cpu_label_font.setPointSize(11)  # Increased from 10
        cpu_label.setFont(cpu_label_font)
        cpu_label.setStyleSheet("color: #6c757d;")
        cpu_label.setMinimumHeight(16)  # Add minimum height to prevent cutoff
        
        if system_name.lower() == "ophiuchus":
            self.oph_cpu_value = QLabel("--")
            self.oph_cpu_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cpu_value_font = QFont()
            cpu_value_font.setPointSize(13)  # Increased from 12
            cpu_value_font.setBold(True)
            self.oph_cpu_value.setFont(cpu_value_font)
            self.oph_cpu_value.setStyleSheet("color: #212529;")
            self.oph_cpu_value.setMinimumHeight(18)  # Add minimum height
            cpu_value = self.oph_cpu_value
        else:
            self.sag_cpu_value = QLabel("--")
            self.sag_cpu_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cpu_value_font = QFont()
            cpu_value_font.setPointSize(13)  # Increased from 12
            cpu_value_font.setBold(True)
            self.sag_cpu_value.setFont(cpu_value_font)
            self.sag_cpu_value.setStyleSheet("color: #212529;")
            self.sag_cpu_value.setMinimumHeight(18)  # Add minimum height
            cpu_value = self.sag_cpu_value
        
        cpu_layout.addWidget(cpu_label)
        cpu_layout.addWidget(cpu_value)
        layout.addLayout(cpu_layout)
        
        # Memory Usage
        mem_layout = QVBoxLayout()
        mem_layout.setSpacing(2)  # Increased from 1
        
        mem_label = QLabel("Memory:")
        mem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mem_label_font = QFont()
        mem_label_font.setPointSize(11)  # Increased from 10
        mem_label.setFont(mem_label_font)
        mem_label.setStyleSheet("color: #6c757d;")
        mem_label.setMinimumHeight(16)  # Add minimum height
        
        if system_name.lower() == "ophiuchus":
            self.oph_mem_value = QLabel("--")
            self.oph_mem_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mem_value_font = QFont()
            mem_value_font.setPointSize(13)  # Increased from 12
            mem_value_font.setBold(True)
            self.oph_mem_value.setFont(mem_value_font)
            self.oph_mem_value.setStyleSheet("color: #212529;")
            self.oph_mem_value.setMinimumHeight(18)  # Add minimum height
            mem_value = self.oph_mem_value
        else:
            self.sag_mem_value = QLabel("--")
            self.sag_mem_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mem_value_font = QFont()
            mem_value_font.setPointSize(13)  # Increased from 12
            mem_value_font.setBold(True)
            self.sag_mem_value.setFont(mem_value_font)
            self.sag_mem_value.setStyleSheet("color: #212529;")
            self.sag_mem_value.setMinimumHeight(18)  # Add minimum height
            mem_value = self.sag_mem_value
        
        mem_layout.addWidget(mem_label)
        mem_layout.addWidget(mem_value)
        layout.addLayout(mem_layout)
        
        # Storage Status
        storage_layout = QVBoxLayout()
        storage_layout.setSpacing(2)  # Increased from 1
        
        storage_label = QLabel("Storage:")
        storage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        storage_label_font = QFont()
        storage_label_font.setPointSize(11)  # Increased from 10
        storage_label.setFont(storage_label_font)
        storage_label.setStyleSheet("color: #6c757d;")
        storage_label.setMinimumHeight(16)  # Add minimum height
        
        if system_name.lower() == "ophiuchus":
            self.oph_storage_value = QLabel("--")
            self.oph_storage_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            storage_value_font = QFont()
            storage_value_font.setPointSize(13)  # Increased from 12
            storage_value_font.setBold(True)
            self.oph_storage_value.setFont(storage_value_font)
            self.oph_storage_value.setStyleSheet("color: #212529;")
            self.oph_storage_value.setMinimumHeight(18)  # Add minimum height
            storage_value = self.oph_storage_value
        else:
            self.sag_storage_value = QLabel("--")
            self.sag_storage_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            storage_value_font = QFont()
            storage_value_font.setPointSize(13)  # Increased from 12
            storage_value_font.setBold(True)
            self.sag_storage_value.setFont(storage_value_font)
            self.sag_storage_value.setStyleSheet("color: #212529;")
            self.sag_storage_value.setMinimumHeight(18)  # Add minimum height
            storage_value = self.sag_storage_value
        
        storage_layout.addWidget(storage_label)
        storage_layout.addWidget(storage_value)
        layout.addLayout(storage_layout)
        
        return section
    

    
    def toggle_state(self):
        """Toggle system monitoring on/off"""
        if self.is_active:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start system monitoring"""
        if self.is_active:
            return
        
        self.is_active = True
        
        # Update control UI
        self.control_status_label.setText("System Monitor: ON")
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
        
        # Start update timer at fixed 1 Hz (1000ms)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.trigger_fetch)
        self.update_timer.start(1000)  # 1000ms = 1 Hz
        
        self.logger.info("System monitoring started at 1 Hz")
    
    def update_logging_indicator(self, is_logging: bool):
        """Update the data logging indicator in the control panel"""
        if is_logging:
            self.logging_indicator_label.setText("📊 Logging")
            self.logging_indicator_label.setStyleSheet("QLabel { color: #28a745; font-weight: bold; }")
        else:
            self.logging_indicator_label.setText("")
            self.logging_indicator_label.setStyleSheet("QLabel { color: #6c757d; }")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Stop timer
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Update control UI
        self.control_status_label.setText("System Monitor: OFF")
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
        
        self.logger.info("System monitoring stopped")
    
    def trigger_fetch(self):
        """Trigger a data fetch"""
        if not self.is_active:
            return
        
        current_time = dt.datetime.now().timestamp()
        if current_time - self.last_fetch_time > 1.0:  # 1 second cooldown
            self.last_fetch_time = current_time
            self.trigger_fetch_signal.emit()
    
    def handle_data_update(self, system_name, data):
        """Handle updated system data"""
        self.system_data[system_name] = data
        self.update_display(system_name, data)
        
        # Track update rate
        self.update_times.append(dt.datetime.now())
    
    def update_display(self, system_name, data):
        """Update the clean display with current system data"""
        if not self.is_active or not hasattr(self, 'oph_cpu_value'):
            return
        
        # Update status header
        self.update_status_header()
        
        # Update clean display
        if system_name == "ophiuchus":
            if hasattr(self, 'oph_cpu_value'):
                if data.valid:
                    self.oph_cpu_value.setText(f"{data.cpu_temp:.1f}°C")
                    self.oph_mem_value.setText(f"{data.mem_used_str}/{data.mem_total_str}")
                    if data.ssd_mounted:
                        storage_text = f"{data.ssd_used}/{data.ssd_total} ✓"
                    else:
                        storage_text = f"{data.ssd_total} ✗"
                    self.oph_storage_value.setText(storage_text)
                else:
                    self.oph_cpu_value.setText("--")
                    self.oph_mem_value.setText("--")
                    self.oph_storage_value.setText("--")
        
        else:  # saggitarius
            if hasattr(self, 'sag_cpu_value'):
                if data.valid:
                    self.sag_cpu_value.setText(f"{data.cpu_temp:.1f}°C")
                    self.sag_mem_value.setText(f"{data.mem_used_str}/{data.mem_total_str}")
                    if data.ssd_mounted:
                        storage_text = f"{data.ssd_used}/{data.ssd_total} ✓"
                    else:
                        storage_text = f"{data.ssd_total} ✗"
                    self.sag_storage_value.setText(storage_text)
                else:
                    self.sag_cpu_value.setText("--")
                    self.sag_mem_value.setText("--")
                    self.sag_storage_value.setText("--")
    
    def update_status_header(self):
        """Update the status header with connection status and last update time"""
        if not hasattr(self, 'connection_label'):
            return
        
        # Check if any system has valid data
        oph_connected = self.system_data['ophiuchus'].valid
        sag_connected = self.system_data['saggitarius'].valid
        
        if oph_connected or sag_connected:
            self.connection_label.setText("Connected")
            self.connection_label.setStyleSheet("QLabel { color: green; }")
            
            # Get latest update time
            latest_time = max(self.system_data['ophiuchus'].last_fetch_time,
                            self.system_data['saggitarius'].last_fetch_time)
            if latest_time > 0:
                update_time = dt.datetime.fromtimestamp(latest_time).strftime("%H:%M:%S")
                self.last_update_label.setText(f"Last Update: {update_time}")
            else:
                self.last_update_label.setText("Last Update: Never")
        else:
            self.connection_label.setText("Disconnected")
            self.connection_label.setStyleSheet("QLabel { color: red; }")
            self.last_update_label.setText("Last Update: Never")
    
    
    def is_monitoring_active(self) -> bool:
        """Check if system monitoring is active"""
        return self.is_active
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate from all clients"""
        total_rate = sum(client.get_data_rate_kbps() for client in self.clients.values())
        return total_rate
    
    def set_data_logging_active(self, is_active: bool):
        """Set the data logging indicator status
        
        Args:
            is_active: Whether data logging is active
        """
        self.update_logging_indicator(is_active)
        
    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop_monitoring()
        
        # Stop worker thread
        if hasattr(self, 'worker_thread'):
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Clean up clients
        for client in self.clients.values():
            client.cleanup()
        
        # Clear data
        self.update_times.clear()
        
        self.logger.info("System monitor widget cleaned up")
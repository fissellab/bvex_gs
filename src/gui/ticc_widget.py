"""
TICC Widget for BVEX Ground Station
Displays real-time TICC drift measurements with time-series plot
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont
import datetime as dt
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from src.data.ticc_client import TICCClient, TICCData


class TICCWorker(QObject):
    """Worker to fetch TICC data in a separate thread"""
    data_updated = pyqtSignal(object)
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    def fetch_data(self):
        """Fetch TICC telemetry data"""
        success = self.client.update_data()
        self.data_updated.emit(self.client.current_data)


class TICCPlotWidget(QWidget):
    """Widget for plotting TICC drift over time"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(6, 3), dpi=80, facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        
        # Create axis
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (minutes ago)', fontsize=9)
        self.ax.set_ylabel('Drift (seconds)', fontsize=9)
        self.ax.set_title('TICC PPS Drift (GPS - OCXO)', fontsize=10, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.tick_params(labelsize=8)
        
        # Data storage for plotting (keep last 10 minutes)
        self.max_points = 600  # 10 minutes at 1Hz
        self.timestamps = deque(maxlen=self.max_points)
        self.intervals = deque(maxlen=self.max_points)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.canvas)
        
        # Adjust plot margins
        self.figure.subplots_adjust(left=0.12, right=0.95, top=0.90, bottom=0.15)
        
        # Initialize empty plot
        self.line, = self.ax.plot([], [], 'b-', linewidth=1.5, markersize=2)
        self.ax.set_xlim(0, 10)  # 10 minutes
        self.ax.set_ylim(-1e-6, 1e-6)  # Default range in seconds
        
        self.canvas.draw()
    
    def add_data_point(self, timestamp: float, interval: float):
        """Add a new data point to the plot"""
        current_time = dt.datetime.now().timestamp()
        
        # Store data
        self.timestamps.append(current_time)
        self.intervals.append(interval)
        
        # Update plot if we have data
        if len(self.timestamps) > 1:
            # Convert timestamps to minutes ago
            times_ago = [(current_time - t) / 60.0 for t in self.timestamps]
            times_ago.reverse()  # Reverse so oldest is on left
            intervals_list = list(self.intervals)
            intervals_list.reverse()
            
            # Update line data
            self.line.set_data(times_ago, intervals_list)
            
            # Auto-scale axes
            if times_ago:
                self.ax.set_xlim(0, max(10, max(times_ago) * 1.1))
            
            if intervals_list:
                interval_range = max(intervals_list) - min(intervals_list)
                if interval_range > 0:
                    margin = interval_range * 0.1
                    self.ax.set_ylim(min(intervals_list) - margin, max(intervals_list) + margin)
                else:
                    # If all values are the same, create a small range around the value
                    value = intervals_list[0]
                    margin = abs(value) * 0.1 if value != 0 else 1e-9
                    self.ax.set_ylim(value - margin, value + margin)
            
            self.canvas.draw_idle()
    
    def clear_plot(self):
        """Clear the plot data"""
        self.timestamps.clear()
        self.intervals.clear()
        self.line.set_data([], [])
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-1e-6, 1e-6)
        self.canvas.draw()


class TICCWidget(QWidget):
    """Widget displaying real-time TICC telemetry data with drift plot"""
    trigger_fetch_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize TICC client
        self.ticc_client = TICCClient()
        
        # Control state
        self.is_active = False
        
        # Data storage
        self.current_data = TICCData()
        self.last_fetch_time = 0
        
        # History for data rate calculation
        self.update_times = deque(maxlen=10)
        
        self.setup_ui()
        self.setup_worker_thread()
        
        self.logger.info("TICC Widget initialized (OFF by default)")
    
    def setup_worker_thread(self):
        """Setup the worker thread for non-blocking data fetching"""
        self.worker_thread = QThread()
        self.worker = TICCWorker(self.ticc_client)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker.data_updated.connect(self.handle_data_update)
        self.trigger_fetch_signal.connect(self.worker.fetch_data)
        
        self.worker_thread.start()
    
    def setup_ui(self):
        """Initialize the clean user interface matching VLBI/GPS style"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("TICC Monitor: OFF")
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
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        self.setMinimumHeight(350)
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add centered message
        message_label = QLabel("TICC Monitor - Waiting for User Input")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        message_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        instruction_label = QLabel('Click "Turn ON" to start TICC monitoring')
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setFont(QFont("Arial", 12))
        instruction_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.container_layout.addStretch()
        self.container_layout.addWidget(message_label)
        self.container_layout.addWidget(instruction_label)
        self.container_layout.addStretch()
    
    def setup_active_display(self):
        """Setup the active TICC display with data fields and plot"""
        # Clear existing widgets
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Status header
        self.status_header = self._create_status_header()
        self.container_layout.addWidget(self.status_header)
        
        # Data section
        data_section = self._create_data_section()
        self.container_layout.addWidget(data_section)
        
        # Plot section
        self.plot_widget = TICCPlotWidget()
        self.container_layout.addWidget(self.plot_widget)
    
    def _create_status_header(self):
        """Create clean TICC connection status header"""
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
        
        # TICC Connected text
        self.status_label = QLabel("TICC Connected")
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
        """Create clean data section with TICC status information"""
        data_frame = QFrame()
        data_frame.setFrameStyle(QFrame.Shape.NoFrame)
        data_frame.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        
        # Main layout for data
        layout = QGridLayout(data_frame)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Current drift value (prominent display)
        drift_label_text = QLabel("Current Drift:")
        drift_label_text.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        drift_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(drift_label_text, 0, 0)
        
        self.drift_value_label = QLabel("-- seconds")
        self.drift_value_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.drift_value_label.setStyleSheet("QLabel { color: #0066cc; }")
        layout.addWidget(self.drift_value_label, 0, 1, 1, 2)
        
        # Status information
        status_label_text = QLabel("Status:")
        status_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(status_label_text, 1, 0)
        self.logging_status_label = QLabel("Unknown")
        self.logging_status_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.logging_status_label, 1, 1)
        
        # Measurement count
        count_label_text = QLabel("Measurements:")
        count_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(count_label_text, 1, 2)
        self.measurement_count_label = QLabel("0")
        self.measurement_count_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.measurement_count_label, 1, 3)
        
        # Last update
        updated_label_text = QLabel("Updated:")
        updated_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(updated_label_text, 2, 0)
        self.last_update_label = QLabel("Never")
        self.last_update_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.last_update_label, 2, 1)
        
        # Update rate
        rate_label_text = QLabel("Rate:")
        rate_label_text.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(rate_label_text, 2, 2)
        self.update_rate_label = QLabel("0.0 Hz")
        self.update_rate_label.setStyleSheet("QLabel { color: black; }")
        layout.addWidget(self.update_rate_label, 2, 3)
        
        return data_frame
    
    def _update_status_display(self, connected):
        """Update the status header display"""
        if not hasattr(self, 'status_label') or not hasattr(self, 'status_dot'):
            return
            
        if connected:
            self.status_label.setText("TICC Connected")
            self.status_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("QLabel { color: #006400; }")
        else:
            self.status_label.setText("TICC Disconnected")
            self.status_label.setStyleSheet("QLabel { color: #8b0000; font-weight: bold; }")
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("QLabel { color: #8b0000; }")
    
    def toggle_state(self):
        """Toggle TICC monitoring on/off"""
        if self.is_active:
            self.stop_ticc()
        else:
            self.start_ticc()
    
    def start_ticc(self):
        """Start TICC telemetry monitoring"""
        if self.is_active:
            return
        
        self.is_active = True
        
        # Update control UI
        self.control_status_label.setText("TICC Monitor: ON")
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
        
        self.logger.info("TICC telemetry monitoring started")
    
    def stop_ticc(self):
        """Stop TICC telemetry monitoring"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Stop timer
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # Update control UI
        self.control_status_label.setText("TICC Monitor: OFF")
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
        
        self.logger.info("TICC telemetry monitoring stopped")
    
    def trigger_fetch(self):
        """Trigger a data fetch"""
        if not self.is_active:
            return
        
        current_time = dt.datetime.now().timestamp()
        if current_time - self.last_fetch_time > 0.5:  # 0.5 second cooldown
            self.last_fetch_time = current_time
            self.trigger_fetch_signal.emit()
    
    def handle_data_update(self, data):
        """Handle updated TICC data"""
        self.current_data = data
        self.update_display()
        
        # Track update rate
        self.update_times.append(dt.datetime.now())
        
        # Add data to plot if valid
        if data.valid and hasattr(self, 'plot_widget'):
            self.plot_widget.add_data_point(data.timestamp, data.interval)
    
    def update_display(self):
        """Update the display with current TICC data"""
        if not self.current_data.valid:
            self.update_display_error()
            return
        
        # Update status header
        connected = self.current_data.valid and self.ticc_client.is_connected()
        self._update_status_display(connected)
        
        # Update drift value (main display)
        drift_text = f"{self.current_data.interval:.6e} seconds"
        if abs(self.current_data.interval) < 1e-6:
            drift_text = f"{self.current_data.interval * 1e9:.3f} nanoseconds"
        elif abs(self.current_data.interval) < 1e-3:
            drift_text = f"{self.current_data.interval * 1e6:.3f} microseconds"
        elif abs(self.current_data.interval) < 1.0:
            drift_text = f"{self.current_data.interval * 1e3:.3f} milliseconds"
        
        self.drift_value_label.setText(drift_text)
        
        # Update logging status
        if self.current_data.logging:
            self.logging_status_label.setText("LOGGING")
            self.logging_status_label.setStyleSheet("QLabel { color: #006400; font-weight: bold; }")
        else:
            self.logging_status_label.setText("NOT LOGGING")
            self.logging_status_label.setStyleSheet("QLabel { color: #ff8c00; font-weight: bold; }")
        
        # Update measurement count
        self.measurement_count_label.setText(f"{self.current_data.measurement_count:,}")
        
        # Update last update time
        if self.current_data.timestamp > 0:
            try:
                timestamp = dt.datetime.fromtimestamp(self.current_data.timestamp)
                time_diff = dt.datetime.now() - timestamp
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
        
        # Set all data to unknown/error
        self.drift_value_label.setText("-- seconds")
        self.logging_status_label.setText("Unknown")
        self.logging_status_label.setStyleSheet("QLabel { color: #666666; }")
        self.measurement_count_label.setText("N/A")
        self.last_update_label.setText("Error")
        self.update_rate_label.setText("0.0 Hz")
    
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
            self.logger.info(f"TICC update frequency changed to {frequency} Hz")
    
    def is_ticc_active(self) -> bool:
        """Check if TICC monitoring is active"""
        return self.is_active
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate in KB/s"""
        return self.ticc_client.get_data_rate_kbps()
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop_ticc()
        
        # Stop worker thread
        if hasattr(self, 'worker_thread'):
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        # Clean up client
        if hasattr(self, 'ticc_client'):
            self.ticc_client.cleanup()
        
        # Clear data
        self.update_times.clear()
        
        # Clear plot
        if hasattr(self, 'plot_widget'):
            self.plot_widget.clear_plot()
        
        self.logger.info("TICC widget cleaned up")
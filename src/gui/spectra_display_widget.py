"""
Spectra Display Widget for BVEX Ground Station
Displays real-time spectrum data from BCP Spectrometer
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
import datetime as dt
from collections import deque

from src.data.bcp_spectrometer_client import BCPSpectrometerClient, SpectrumData


class SpectraDisplayWidget(QWidget):
    """Widget displaying real-time spectrum data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize spectrometer client
        self.spectrometer_client = BCPSpectrometerClient()
        
        # Data storage for plotting
        self.spectrum_data = None
        self.last_update_time = None
        
        # History buffer for data rate calculation
        self.update_times = deque(maxlen=10)
        
        # Create frequency axis exactly matching read_latest_data.py
        fs = 3932.16 / 2
        Nfft = 2**11  # 2048 points
        fbins = np.arange(-Nfft // 2, Nfft // 2)
        df = fs / Nfft
        faxis = fbins * df + fs / 2
        # Don't flip the frequency axis - we want it ascending from ~20.96 to ~22.93 GHz
        self.freq_ghz = faxis/1000 + 21  # Convert to GHz with 21 GHz offset
        
        print(f"Frequency axis: {self.freq_ghz[0]:.5f} to {self.freq_ghz[-1]:.5f} GHz")
        
        self.setup_ui()
        self.setup_update_timer()
    
    def setup_ui(self):
        """Initialize the matplotlib figure and canvas"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        layout.setSpacing(5)  # Reduced spacing
        
        # Create info panel
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)
        
        # Status labels
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("QLabel { color: red; }")
        
        self.spec_type_label = QLabel("Type: Unknown")
        self.spec_type_label.setFont(QFont("Arial", 10))
        
        self.data_rate_label = QLabel("Rate: 0.0 Hz")
        self.data_rate_label.setFont(QFont("Arial", 10))
        
        self.points_label = QLabel("Points: 0")
        self.points_label.setFont(QFont("Arial", 10))
        
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.spec_type_label)
        info_layout.addWidget(self.data_rate_label)
        info_layout.addWidget(self.points_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # Create matplotlib figure (more compact)
        self.figure = Figure(figsize=(10, 6), tight_layout=True)  # Increased width, reasonable height
        self.figure.patch.set_facecolor('white')  # Clean background
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)  # Minimum height
        
        layout.addWidget(self.canvas, 1)  # Give canvas all remaining space
        self.setLayout(layout)
        
        # Initial plot setup
        self.setup_initial_plot()
    
    def setup_initial_plot(self):
        """Setup initial empty plot"""
        self.ax.clear()
        self.ax.set_title("BCP Spectrometer - No Data", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Channel", fontsize=12)
        self.ax.set_ylabel("Power", fontsize=12)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(-1, 1)
        
        # Add placeholder text
        self.ax.text(0.5, 0.5, 'Waiting for spectrum data...', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes, fontsize=14, color='gray')
        
        self.canvas.draw()
    
    def setup_update_timer(self):
        """Setup timer for regular spectrum updates at 1Hz"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrum)
        self.timer.start(1000)  # 1 second = 1 Hz
    
    def update_spectrum(self):
        """Update spectrum display with new data"""
        # Get new spectrum data
        new_spectrum = self.spectrometer_client.get_spectrum()
        
        if new_spectrum and new_spectrum.valid and len(new_spectrum.data) > 0:
            self.spectrum_data = new_spectrum
            self.last_update_time = dt.datetime.now()
            
            # Update rate calculation
            self.update_times.append(self.last_update_time)
            
            # Update status labels
            self.update_status_labels()
            
            # Update plot
            self.plot_spectrum()
            
        else:
            # Update status for failed/invalid data
            self.update_status_labels(failed=True)
    
    def update_status_labels(self, failed=False):
        """Update the status information labels"""
        if failed or not self.spectrum_data or not self.spectrum_data.valid:
            self.status_label.setText("Status: Disconnected")
            self.status_label.setStyleSheet("QLabel { color: red; }")
            self.spec_type_label.setText("Type: Unknown")
            self.data_rate_label.setText("Rate: 0.0 Hz")
            self.points_label.setText("Points: 0")
        else:
            # Connected and getting data
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet("QLabel { color: green; }")
            
            # Spectrum type
            spec_type = self.spectrum_data.type
            if spec_type == '120KHZ':
                type_text = f"Type: 120kHz ({self.spectrum_data.freq_start:.3f}-{self.spectrum_data.freq_end:.3f} GHz)"
            else:
                type_text = f"Type: {spec_type}"
            self.spec_type_label.setText(type_text)
            
            # Data rate calculation
            if len(self.update_times) >= 2:
                time_diff = (self.update_times[-1] - self.update_times[0]).total_seconds()
                rate = (len(self.update_times) - 1) / time_diff
                self.data_rate_label.setText(f"Rate: {rate:.1f} Hz")
            else:
                self.data_rate_label.setText("Rate: Calculating...")
            
            # Points count
            self.points_label.setText(f"Points: {self.spectrum_data.points}")
    
    def plot_spectrum(self):
        """Plot the current spectrum data with proper processing"""
        if not self.spectrum_data or not self.spectrum_data.valid:
            return
        
        self.ax.clear()
        
        # Prepare data for plotting
        raw_data = np.array(self.spectrum_data.data)
        
        # Apply the same processing as in read_latest_data.py
        # Convert to dB scale with better handling of zeros
        # Find minimum non-zero value for proper scaling
        non_zero_mask = raw_data > 0
        if np.any(non_zero_mask):
            min_positive = np.min(raw_data[non_zero_mask])
            # Use a floor value that's 1000x smaller than the minimum positive value
            floor_value = min_positive / 1000.0
        else:
            # If all values are zero, use a very small default
            floor_value = 1e-12
            
        # Apply log10 with proper floor to avoid -inf
        spectrum_db = 10 * np.log10(np.maximum(raw_data, floor_value))
        
        # Flip the spectrum (as done in read_latest_data.py)
        spectrum_db = np.flip(spectrum_db)
        
        # Plot spectrum
        self.ax.plot(self.freq_ghz, spectrum_db, 'b-', linewidth=1, alpha=0.8)
        
        # Configure plot based on spectrum type
        if self.spectrum_data.type == '120KHZ':
            # High-resolution water maser spectrum
            title = f"120kHz Water Maser Spectrum - {self.spectrum_data.freq_start:.3f}-{self.spectrum_data.freq_end:.3f} GHz"
            ylabel = "Power (dB above baseline)"
            
            # For 120kHz data, we might need different frequency handling
            # Keep the original frequency range if available
            if self.spectrum_data.freq_start and self.spectrum_data.freq_end:
                # Create frequency axis based on actual frequency range
                freq_120k = np.linspace(self.spectrum_data.freq_start, 
                                       self.spectrum_data.freq_end, 
                                       len(spectrum_db))
                self.ax.clear()
                self.ax.plot(freq_120k, spectrum_db, 'b-', linewidth=1, alpha=0.8)
                self.ax.set_xlabel("Frequency (GHz)", fontsize=11)
            else:
                self.ax.set_xlabel("Frequency (GHz)", fontsize=11)
            
        elif self.spectrum_data.type == 'STANDARD':
            # Standard spectrum
            title = "Standard Spectrum (Full IF Bandwidth)"
            ylabel = "Power (dB arb.)"
            self.ax.set_xlabel("Frequency (GHz)", fontsize=11)
        else:
            title = f"{self.spectrum_data.type} Spectrum"
            ylabel = "Power (dB arb.)"
            self.ax.set_xlabel("Frequency (GHz)", fontsize=11)
        
        # Add timestamp to title
        timestamp_str = dt.datetime.fromtimestamp(self.spectrum_data.timestamp).strftime("%H:%M:%S")
        title += f" - {timestamp_str}"
        
        # Set labels and title
        self.ax.set_title(title, fontsize=12, fontweight='bold')
        self.ax.set_ylabel(ylabel, fontsize=11)
        
        # Configure grid and ticks
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.tick_params(labelsize=9)
        
        # Auto-scale with some padding, handling the case of mostly uniform data
        if len(spectrum_db) > 0 and not np.any(np.isnan(spectrum_db)) and not np.any(np.isinf(spectrum_db)):
            y_min, y_max = np.min(spectrum_db), np.max(spectrum_db)
            y_range = y_max - y_min
            
            if y_range > 0.1:  # If there's significant variation
                padding = 0.05 * y_range
                self.ax.set_ylim(y_min - padding, y_max + padding)
            else:
                # If the data is mostly flat, show a reasonable range around the mean
                y_mean = np.mean(spectrum_db)
                self.ax.set_ylim(y_mean - 1.0, y_mean + 1.0)
            
            # Set frequency axis limits
            if self.spectrum_data.type == 'STANDARD':
                self.ax.set_xlim(self.freq_ghz[0], self.freq_ghz[-1])
            elif self.spectrum_data.type == '120KHZ' and self.spectrum_data.freq_start and self.spectrum_data.freq_end:
                self.ax.set_xlim(self.spectrum_data.freq_start, self.spectrum_data.freq_end)
        else:
            # Fallback for problematic data
            self.ax.set_ylim(-50, 10)  # Reasonable dB range
            if self.spectrum_data.type == 'STANDARD':
                self.ax.set_xlim(21, 23)  # 21-23 GHz range
        
        # Add data quality info
        non_zero_count = np.sum(raw_data > 0)
        total_count = len(raw_data)
        
        info_text = f"Active channels: {non_zero_count}/{total_count}"
        if floor_value < 1e-6:
            info_text += f" | Floor: {floor_value:.2e}"
            
        self.ax.text(0.02, 0.02, info_text, 
                    transform=self.ax.transAxes, fontsize=9, 
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Add baseline info for 120kHz data
        if self.spectrum_data.type == '120KHZ' and self.spectrum_data.baseline is not None:
            self.ax.text(0.02, 0.98, f"Baseline: {self.spectrum_data.baseline:.2f} dB", 
                        transform=self.ax.transAxes, fontsize=10, 
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Refresh canvas
        self.canvas.draw()
    
    def get_spectrum_data(self):
        """Get current spectrum data for external use"""
        return self.spectrum_data
    
    def is_connected(self):
        """Check if spectrometer client is connected"""
        return self.spectrometer_client.is_connected() 
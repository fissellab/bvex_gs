"""
Spectra Display Widget for BVEX Ground Station
Displays real-time spectrum data from BCP Spectrometer
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy, QComboBox, QSlider
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont
import datetime as dt
from collections import deque
import logging

from src.data.bcp_spectrometer_client import BCPSpectrometerClient, SpectrumData


class SpectrometerWorker(QObject):
    """Worker to fetch spectrometer data in a separate thread"""
    spectrum_updated = pyqtSignal(object)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def fetch_spectrum(self):
        """Fetch spectrum data"""
        new_spectrum = self.client.get_spectrum()
        self.spectrum_updated.emit(new_spectrum)


class SpectraDisplayWidget(QWidget):
    """Widget displaying real-time spectrum data"""
    trigger_fetch_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        # Initialize spectrometer client (will be used in worker thread)
        self.spectrometer_client = BCPSpectrometerClient()
        
        # Control state
        self.is_active = False
        
        # Data storage for plotting
        self.spectrum_data = None
        self.last_fetch_time = 0
        
        # History buffer for data rate calculation
        self.update_times = deque(maxlen=10)
        
        # Data storage for integrated power plot - Option 1: Reduced buffer size
        self.power_times = deque(maxlen=100) # Store ~10 seconds of data at 10Hz (reduced from 200)
        self.power_values = deque(maxlen=100)
        
        # Integration time control for power plot
        self.integration_time_sec = 2.0  # Default integration time in seconds
        self.power_accumulator = []  # Temporary storage for power values during integration
        self.integration_start_time = None  # Track when integration period started
        self.integrated_plot_times = deque(maxlen=100)  # For the actual plot points
        self.integrated_plot_values = deque(maxlen=100)  # For the actual plot points
        
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
        self.setup_worker_thread()
        # Don't start timer initially - only when activated
    
    def setup_worker_thread(self):
        """Setup the worker thread for non-blocking data fetching"""
        self.worker_thread = QThread()
        self.worker = SpectrometerWorker(self.spectrometer_client)
        self.worker.moveToThread(self.worker_thread)

        self.worker.spectrum_updated.connect(self.handle_spectrum_update)
        self.trigger_fetch_signal.connect(self.worker.fetch_spectrum)

        self.worker_thread.start()

    def trigger_fetch(self):
        """Trigger a fetch, respecting a cooldown"""
        if not self.is_active:
            return
            
        current_time = dt.datetime.now().timestamp()
        if current_time - self.last_fetch_time > 1.0: # 1 second cooldown
            self.last_fetch_time = current_time
            self.trigger_fetch_signal.emit()

    def stop_worker(self):
        """Stop the worker thread"""
        self.worker_thread.quit()
        self.worker_thread.wait()
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        # Stop spectrometer and worker thread
        self.stop_spectrometer()
        self.stop_worker()
        
        # Clean up spectrometer client
        if hasattr(self, 'spectrometer_client'):
            self.spectrometer_client.cleanup()
        
        # Clear data buffers
        self.spectrum_data = None
        self.update_times.clear()
        self.power_times.clear()
        self.power_values.clear()
        self.integrated_plot_times.clear()
        self.integrated_plot_values.clear()
        self.power_accumulator.clear()
        
        self.logger.info("Spectra display widget cleaned up")

    def setup_ui(self):
        """Initialize the matplotlib figure and canvas"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        layout.setSpacing(5)  # Reduced spacing
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.control_status_label = QLabel("Spectrometer: OFF")
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
        
        layout.addLayout(control_layout)
        
        # Create info panel
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)
        
        # Status labels
        self.status_label = QLabel("Status: Off")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("QLabel { color: gray; }")
        
        self.spec_type_label = QLabel("Type: N/A")
        self.spec_type_label.setFont(QFont("Arial", 10))
        self.spec_type_label.setStyleSheet("QLabel { color: gray; }")
        
        self.data_rate_label = QLabel("Rate: 0.0 Hz")
        self.data_rate_label.setFont(QFont("Arial", 10))
        self.data_rate_label.setStyleSheet("QLabel { color: gray; }")
        
        self.points_label = QLabel("Points: 0")
        self.points_label.setFont(QFont("Arial", 10))
        self.points_label.setStyleSheet("QLabel { color: gray; }")
        
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.spec_type_label)
        info_layout.addWidget(self.data_rate_label)
        info_layout.addWidget(self.points_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # Create matplotlib figure with two subplots
        self.figure = Figure(figsize=(10, 8), tight_layout=True)
        self.figure.patch.set_facecolor('white')
        self.ax_spectrum, self.ax_power = self.figure.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})
        
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(400) # Increased height for two plots
        
        layout.addWidget(self.canvas, 1)
        
        # Add integration time control below the plot
        integration_layout = QHBoxLayout()
        integration_layout.setContentsMargins(10, 5, 10, 5)
        
        # Integration time label
        integration_label = QLabel("Integration Time:")
        integration_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        integration_layout.addWidget(integration_label)
        
        # Integration time slider (1-10 seconds)
        self.integration_slider = QSlider(Qt.Orientation.Horizontal)
        self.integration_slider.setMinimum(10)  # 1.0 second (in tenths)
        self.integration_slider.setMaximum(100)  # 10.0 seconds (in tenths)
        self.integration_slider.setValue(20)  # Default 2.0 seconds
        self.integration_slider.setMinimumWidth(200)
        self.integration_slider.valueChanged.connect(self.on_integration_time_changed)
        integration_layout.addWidget(self.integration_slider)
        
        # Integration time value display
        self.integration_value_label = QLabel("2.0 sec")
        self.integration_value_label.setFont(QFont("Arial", 10))
        self.integration_value_label.setMinimumWidth(60)
        integration_layout.addWidget(self.integration_value_label)
        
        integration_layout.addStretch()
        layout.addLayout(integration_layout)
        
        # Add description label below the slider
        description_layout = QHBoxLayout()
        description_layout.setContentsMargins(10, 0, 10, 5)
        
        description_label = QLabel("Adjust integration time")
        description_label.setFont(QFont("Arial", 9))
        description_label.setStyleSheet("QLabel { color: #6c757d; }")  # Muted gray color
        description_layout.addWidget(description_label)
        description_layout.addStretch()
        
        layout.addLayout(description_layout)
        
        self.setLayout(layout)
        
        # Initial plot setup
        self.setup_static_display()
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_spectrometer()
        else:
            self.start_spectrometer()
    
    def start_spectrometer(self):
        """Start spectrometer data fetching"""
        if not self.is_active:
            self.is_active = True
            self.control_status_label.setText("Spectrometer: ON")
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
            
            # Setup active display and start timer
            self.setup_active_display()
            
            # Clear any old integration plot data when starting fresh
            self.clear_integration_plot_data()
            
            self.setup_update_timer()
    
    def stop_spectrometer(self):
        """Stop spectrometer data fetching and show static display"""
        if self.is_active:
            self.is_active = False
            self.control_status_label.setText("Spectrometer: OFF")
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
            
            # Stop timer and show static display
            if hasattr(self, 'timer'):
                self.timer.stop()
            self.setup_static_display()
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        # Update status labels to show off state
        self.status_label.setText("Status: Off")
        self.status_label.setStyleSheet("QLabel { color: gray; }")
        self.spec_type_label.setText("Type: N/A")
        self.spec_type_label.setStyleSheet("QLabel { color: gray; }")
        self.data_rate_label.setText("Rate: 0.0 Hz")
        self.data_rate_label.setStyleSheet("QLabel { color: gray; }")
        self.points_label.setText("Points: 0")
        self.points_label.setStyleSheet("QLabel { color: gray; }")
        
        # Setup static plots
        # Spectrum plot
        self.ax_spectrum.clear()
        self.ax_spectrum.set_title("Spectrometer - Waiting for User Input", fontsize=14, fontweight='bold', color='gray')
        self.ax_spectrum.set_xlabel("Frequency (GHz)", fontsize=12)
        self.ax_spectrum.set_ylabel("Power (dB)", fontsize=12)
        self.ax_spectrum.grid(True, alpha=0.3)
        
        # Rotate x-axis labels to prevent overlapping
        self.ax_spectrum.tick_params(axis='x', labelrotation=45, labelsize=9)
        
        self.ax_spectrum.text(0.5, 0.5, 'Click "Turn ON" to start\nspectrum data acquisition', 
                              horizontalalignment='center', verticalalignment='center',
                              transform=self.ax_spectrum.transAxes, fontsize=16, color='gray', weight='bold')

        # Integrated power plot
        self.ax_power.clear()
        self.ax_power.set_title("Integrated Power - Waiting for User Input", fontsize=12, color='gray')
        self.ax_power.set_xlabel("Time", fontsize=10)
        self.ax_power.set_ylabel("Power (dB)", fontsize=10)
        self.ax_power.grid(True, alpha=0.3)
        self.ax_power.text(0.5, 0.5, 'Waiting for activation', 
                          horizontalalignment='center', verticalalignment='center',
                          transform=self.ax_power.transAxes, fontsize=12, color='gray')
        
        # Ensure proper spacing between subplots to accommodate rotated labels
        self.figure.subplots_adjust(bottom=0.15, hspace=0.4)
        
        self.canvas.draw()
    
    def setup_active_display(self):
        """Setup the active display with normal plot titles"""
        # Spectrum plot
        self.ax_spectrum.clear()
        self.ax_spectrum.set_title("BCP Spectrometer - No Data", fontsize=14, fontweight='bold')
        self.ax_spectrum.set_xlabel("Frequency (GHz)", fontsize=12)
        self.ax_spectrum.set_ylabel("Power (dB)", fontsize=12)
        self.ax_spectrum.grid(True, alpha=0.3)
        
        # Rotate x-axis labels to prevent overlapping
        self.ax_spectrum.tick_params(axis='x', labelrotation=45, labelsize=9)
        
        self.ax_spectrum.text(0.5, 0.5, 'Waiting for spectrum data...', 
                              horizontalalignment='center', verticalalignment='center',
                              transform=self.ax_spectrum.transAxes, fontsize=14, color='gray')

        # Integrated power plot
        self.ax_power.clear()
        self.ax_power.set_title("Integrated Power", fontsize=12)
        self.ax_power.set_xlabel("Time", fontsize=10)
        self.ax_power.set_ylabel("Power (dB)", fontsize=10)
        self.ax_power.grid(True, alpha=0.3)
        
        # Ensure proper spacing between subplots to accommodate rotated labels
        self.figure.subplots_adjust(bottom=0.15, hspace=0.4)
        
        self.canvas.draw()
    
    def setup_update_timer(self):
        """Setup timer for regular spectrum updates"""
        if not hasattr(self, 'timer'):
            self.timer = QTimer()
            self.timer.timeout.connect(self.trigger_fetch)
        self.timer.start(2000)  # 2000 ms = 0.5 Hz
    
    def handle_spectrum_update(self, new_spectrum):
        """Update spectrum display with new data"""
        # Only process updates if spectrometer is active
        if not self.is_active:
            return
            
        # Get new spectrum data
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
        
        # Check for data length mismatch before plotting
        if len(self.spectrum_data.data) != len(self.freq_ghz) and self.spectrum_data.type == 'STANDARD':
             self.logger.warning("Mismatch between standard data length and frequency axis. Skipping plot.")
             return
        
        self.ax_spectrum.clear()
        
        # Prepare data for plotting
        raw_data = np.array(self.spectrum_data.data)
        
        # Handle data processing based on spectrum type
        if self.spectrum_data.type == 'STANDARD':
            # STANDARD data comes as linear power values - convert to dB
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
            
            # Integrated power calculation for STANDARD data
            integrated_power = np.sum(raw_data)
            integrated_power_db = 10 * np.log10(np.maximum(integrated_power, floor_value))
            
        elif self.spectrum_data.type == '120KHZ':
            # 120KHZ data is already in dB format (baseline-subtracted) - use directly
            spectrum_db = raw_data.copy()
            
            # For integrated power, we need to convert back to linear, sum, then convert to dB
            # Since data is baseline-subtracted dB, we need to add back the baseline first
            if self.spectrum_data.baseline is not None:
                linear_data = 10**((raw_data + self.spectrum_data.baseline) / 10.0)
                integrated_power = np.sum(linear_data)
                integrated_power_db = 10 * np.log10(np.maximum(integrated_power, 1e-12))
            else:
                # Fallback if no baseline info
                integrated_power_db = np.sum(raw_data)  # Simple sum of dB values
                
        else:
            self.logger.warning(f"Unknown spectrum type: {self.spectrum_data.type}")
            return
        
        # Update power tracking
        current_time = dt.datetime.now()
        self.power_times.append(current_time)
        self.power_values.append(integrated_power_db)
        
        # Handle power integration for plot
        self.handle_power_integration(integrated_power_db, current_time)
        
        # --- Plotting ---
        self.ax_spectrum.clear()
        self.ax_power.clear()
        
        # Plot spectrum data
        if self.spectrum_data.type == 'STANDARD':
            if len(spectrum_db) == len(self.freq_ghz):
                self.ax_spectrum.plot(self.freq_ghz, spectrum_db, 'b-', linewidth=1, alpha=0.8)
                self.ax_spectrum.set_xlim(self.freq_ghz[0], self.freq_ghz[-1])
            else:
                self.logger.warning("Mismatch in standard spectrum data length. Skipping plot.")
                return 
        elif self.spectrum_data.type == '120KHZ':
            if self.spectrum_data.freq_start is not None and self.spectrum_data.freq_end is not None:
                freq_120k = np.linspace(self.spectrum_data.freq_start, self.spectrum_data.freq_end, len(spectrum_db))
                self.ax_spectrum.plot(freq_120k, spectrum_db, 'b-', linewidth=1, alpha=0.8)
                self.ax_spectrum.set_xlim(self.spectrum_data.freq_start, self.spectrum_data.freq_end)
            else:
                 self.logger.warning("120kHz spectrum missing frequency range. Skipping plot.")
                 return
        
        # Set titles and labels for spectrum
        title = f"{self.spectrum_data.type} Spectrum"
        timestamp_str = self.last_update_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.ax_spectrum.set_title(f"{title} - {timestamp_str}", fontsize=12, fontweight='bold')
        self.ax_spectrum.set_xlabel("Frequency (GHz)", fontsize=11)
        self.ax_spectrum.set_ylabel("Power (dB arb.)", fontsize=11)
        self.ax_spectrum.grid(True, alpha=0.3, linestyle='--')
        
        # Rotate x-axis labels to prevent overlapping
        self.ax_spectrum.tick_params(axis='x', labelrotation=45, labelsize=9)
        
        # Ensure proper spacing between subplots to accommodate rotated labels
        self.figure.subplots_adjust(bottom=0.15, hspace=0.4)
        
        # Dynamic Y-axis for spectrum - different logic for STANDARD vs 120KHZ
        if self.spectrum_data.type == 'STANDARD':
            # For STANDARD spectra: Focus on interesting spectral features, not noise floor
            y_min_data, y_max_data = np.min(spectrum_db), np.max(spectrum_db)
            
            # Use more aggressive percentiles to focus on spectral features
            y_20th = np.percentile(spectrum_db, 20)  # Cut off bottom 20% (noise floor)
            y_95th = np.percentile(spectrum_db, 95)  # Keep most peaks but avoid extreme outliers
            
            # Use a fixed 12 dB window, positioned to capture the interesting range
            target_range = 12.0  # dB - good detail level
            
            # Center the window on the 75th percentile (biased toward peaks)
            y_center = np.percentile(spectrum_db, 75)
            y_min = y_center - target_range * 0.4  # 40% below center
            y_max = y_center + target_range * 0.6  # 60% above center
            
            # Ensure we don't cut off the 95th percentile peak
            if y_95th > y_max:
                # Shift window up to include important peaks
                shift = y_95th - y_max + 1.0
                y_min += shift
                y_max += shift
                
            # Ensure we show at least down to the 20th percentile 
            if y_20th < y_min:
                # Only shift down if the range is reasonable
                shift_down = y_min - y_20th
                if shift_down <= 3.0:  # Only minor adjustment
                    y_min = y_20th - 0.5
            
            self.ax_spectrum.set_ylim(y_min, y_max)
            
        elif self.spectrum_data.type == '120KHZ':
            # For 120KHZ spectra: Use full range since it's baseline-subtracted (should be small range already)
            y_min, y_max = np.min(spectrum_db), np.max(spectrum_db)
            y_range = y_max - y_min
            padding = 0.05 * y_range if y_range > 0.1 else 0.5
            self.ax_spectrum.set_ylim(y_min - padding, y_max + padding)

        # Plot integrated power - simplified approach for better visibility
        if self.integrated_plot_times:
            # Filter to show only recent data (last 5 minutes maximum)
            current_time = dt.datetime.now()
            time_cutoff = current_time - dt.timedelta(minutes=5)
            
            # Find indices of data within the time window
            recent_indices = []
            recent_times = []
            recent_values = []
            
            for i, time_point in enumerate(self.integrated_plot_times):
                if time_point >= time_cutoff:
                    recent_indices.append(i)
                    recent_times.append(time_point)
                    recent_values.append(self.integrated_plot_values[i])
            
            if recent_times:
                # Use simple x-axis indexing for recent data only
                x_indices = list(range(len(recent_times)))
                self.ax_power.plot(x_indices, recent_values, 'r-', linewidth=1.5)
                
                # Show evenly spaced time labels across the recent data range
                if len(recent_times) > 1:
                    # Determine the number of ticks to show (max 5)
                    num_ticks = min(5, len(recent_times))
                    
                    # Calculate evenly spaced indices across the recent data length
                    indices = np.linspace(0, len(recent_times) - 1, num_ticks, dtype=int)
                    
                    tick_labels = [recent_times[int(i)].strftime('%H:%M:%S') for i in indices]
                    self.ax_power.set_xticks(indices)
                    self.ax_power.set_xticklabels(tick_labels, rotation=45, ha='right')
                
                # Use recent values for Y-axis scaling
                plot_values_for_scaling = recent_values
            else:
                # No recent data to plot
                plot_values_for_scaling = []
        else:
            plot_values_for_scaling = []
        
        self.ax_power.set_title(f"Integrated Power ({self.integration_time_sec:.1f}s integration)", fontsize=12)
        self.ax_power.set_xlabel("Time", fontsize=10)
        self.ax_power.set_ylabel("Power (dB)", fontsize=10)
        self.ax_power.grid(True, alpha=0.3)
        
        # Disable the scientific notation offset on y-axis for better readability
        self.ax_power.ticklabel_format(useOffset=False, axis='y')
        
        # Dynamic Y-axis for power - make changes more visible using only recent data
        if plot_values_for_scaling:
            p_min, p_max = np.min(plot_values_for_scaling), np.max(plot_values_for_scaling)
            p_range = p_max - p_min
            if p_range > 0.01:  # If there's meaningful variation
                padding = 0.05 * p_range  # Smaller padding to show changes better
            else:
                padding = 0.1  # Minimal padding for flat signals
            self.ax_power.set_ylim(p_min - padding, p_max + padding)
            
        self.canvas.draw()
    
    def get_spectrum_data(self):
        """Return the latest spectrum data"""
        return self.spectrum_data
    
    def is_connected(self):
        """Check if spectrometer client is connected"""
        return self.spectrometer_client.is_connected()
    
    def set_request_rate(self, rate_hz):
        """Set the spectrum data request rate."""
        self.timer.setInterval(int(1000 / rate_hz))
    
    def is_spectrometer_active(self) -> bool:
        """Return whether spectrometer is currently active"""
        return self.is_active
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate from spectrometer client in kB/s"""
        if not self.is_active:
            return 0.0
        return self.spectrometer_client.get_data_rate_kbps()
    
    def on_integration_time_changed(self, value):
        """Handle integration time slider changes"""
        self.integration_time_sec = value / 10.0  # Convert from tenths to seconds
        self.integration_value_label.setText(f"{self.integration_time_sec:.1f} sec")
        
        # Clear all plot data when integration time changes since old data is no longer relevant
        self.clear_integration_plot_data()
    
    def reset_integration(self):
        """Reset the integration accumulator and start time"""
        self.power_accumulator.clear()
        self.integration_start_time = None
    
    def clear_integration_plot_data(self):
        """Clear the integrated plot data (used when settings change or restarting)"""
        self.integrated_plot_times.clear()
        self.integrated_plot_values.clear()
        self.reset_integration()
    
    def handle_power_integration(self, integrated_power_db, current_time):
        """Handle integration of power values over the specified time period"""
        # Initialize integration period if needed
        if self.integration_start_time is None:
            self.integration_start_time = current_time
            self.power_accumulator.clear()
        
        # Add current power reading to accumulator
        self.power_accumulator.append(integrated_power_db)
        
        # Check if integration period is complete
        time_elapsed = (current_time - self.integration_start_time).total_seconds()
        
        if time_elapsed >= self.integration_time_sec:
            # Calculate integrated power over the period
            if self.power_accumulator:
                # Average the accumulated power readings
                averaged_power = np.mean(self.power_accumulator)
                
                # Add to plot data
                self.integrated_plot_times.append(current_time)
                self.integrated_plot_values.append(averaged_power)
                
                # Periodically clean old data to prevent memory bloat
                self.clean_old_plot_data(current_time)
                
                # Reset for next integration period
                self.reset_integration()
    
    def clean_old_plot_data(self, current_time):
        """Remove plot data older than 10 minutes to prevent memory bloat"""
        time_cutoff = current_time - dt.timedelta(minutes=10)
        
        # Remove old entries from the beginning of the deques
        while self.integrated_plot_times and self.integrated_plot_times[0] < time_cutoff:
            self.integrated_plot_times.popleft()
            self.integrated_plot_values.popleft() 
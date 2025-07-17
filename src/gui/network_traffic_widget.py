"""
Network Traffic Monitor Widget for BVEX Ground Station
Monitors total network bandwidth usage across all active clients and widgets
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QProgressBar, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from typing import Dict, Any

class NetworkTrafficWidget(QWidget):
    """Widget for monitoring total network bandwidth usage across all clients"""
    
    def __init__(self, parent=None, pointing_window=None, telescope_data_window=None, housekeeping_window=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # References to all windows to access their widgets
        self.pointing_window = pointing_window
        self.telescope_data_window = telescope_data_window  
        self.housekeeping_window = housekeeping_window
        
        # Bandwidth limit (150 kb/s = 18.75 KB/s since 1 byte = 8 bits)
        self.bandwidth_limit_kbps = 18.75  # Changed from 150.0
        
        # Current data
        self.current_total_kbps = 0.0
        self.client_rates = {}  # Dictionary to store individual client rates
        
        self.setup_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_bandwidth_display)
        self.update_timer.start(1000)  # Update every second
        
        self.logger.info("Network Traffic Monitor initialized - monitoring all active clients")
    
    def setup_ui(self):
        """Initialize the network traffic monitoring interface"""
        # Main layout with adjusted spacing and margins for better visibility
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(3)  # Increased from 2
        main_layout.setContentsMargins(6, 6, 6, 6)  # Increased from 4
        
        # Create main container with styling
        self.container = QFrame()
        self.container.setFrameStyle(QFrame.Shape.StyledPanel)
        self.container.setStyleSheet("""
            QFrame {
                border: 2px solid #333333;
                border-radius: 6px;
                background-color: #f8f9fa;
                padding: 6px;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(4)  # Increased from 2
        container_layout.setContentsMargins(6, 4, 6, 4)  # Increased from 4, 3, 4, 3
        
        # Title - readable size
        title_label = QLabel("🌐 Network Traffic Monitor")
        title_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))  # Increased from 8
        title_label.setStyleSheet("QLabel { color: #495057; border: none; background: transparent; }")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setMinimumHeight(18)  # Increased from 15
        container_layout.addWidget(title_label)
        
        # Main info row - horizontal layout with current usage, progress bar, and limit
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)  # Increased from 6
        
        # Current usage - readable font size
        self.current_usage_label = QLabel("0.0 KB/s")
        self.current_usage_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))  # Increased from 10
        self.current_usage_label.setStyleSheet("QLabel { color: #28a745; border: none; background: transparent; }")
        self.current_usage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_usage_label.setMinimumWidth(70)  # Increased from 60
        self.current_usage_label.setMinimumHeight(24)  # Increased from 20
        
        # Progress bar showing percentage of limit used
        self.usage_progress = QProgressBar()
        self.usage_progress.setMinimum(0)
        self.usage_progress.setMaximum(1000)  # Use 1000 for better precision (percentage * 10)
        self.usage_progress.setValue(0)
        self.usage_progress.setTextVisible(False)  # Hide text to avoid confusion
        self.usage_progress.setMinimumWidth(100)  # Increased from 80
        self.usage_progress.setMinimumHeight(20)  # Increased from 16
        self.usage_progress.setMaximumHeight(20)
        self.usage_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                background-color: #e9ecef;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 2px;
            }
        """)
        
        # Limit display with percentage - compact layout
        limit_layout = QVBoxLayout()
        limit_layout.setSpacing(1)
        
        # Show just the percentage - more compact
        self.percentage_label = QLabel("0%")
        self.percentage_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.percentage_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percentage_label.setMinimumHeight(16)
        self.percentage_label.setMinimumWidth(35)
        
        # Small limit label
        self.limit_label = QLabel("18.8 KB/s")
        self.limit_label.setFont(QFont("Arial", 7))
        self.limit_label.setStyleSheet("QLabel { color: #adb5bd; border: none; background: transparent; }")
        self.limit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.limit_label.setMinimumHeight(10)
        
        limit_layout.addWidget(self.percentage_label)
        limit_layout.addWidget(self.limit_label)
        
        # Refresh button - icon only
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 2px;
                border-radius: 3px;
                font-size: 12px;
                min-width: 22px;
                min-height: 22px;
                max-width: 22px;
                max-height: 22px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.refresh_btn.clicked.connect(self.force_update)
        
        # Add widgets to horizontal layout
        info_layout.addWidget(self.current_usage_label)
        info_layout.addWidget(self.usage_progress, 1)  # Give progress bar more space
        info_layout.addLayout(limit_layout)
        info_layout.addWidget(self.refresh_btn)
        
        container_layout.addLayout(info_layout)
        
        # Status line showing top client - readable font
        self.top_client_label = QLabel("No active clients")
        self.top_client_label.setFont(QFont("Arial", 8))  # Increased from 7
        self.top_client_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
        self.top_client_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_client_label.setMinimumHeight(16)  # Increased from 12
        container_layout.addWidget(self.top_client_label)
        
        main_layout.addWidget(self.container)
        
        # Set widget size with more height to accommodate all elements properly
        self.setMinimumSize(380, 130)  # Increased from 350, 100
        self.setMaximumSize(420, 150)  # Increased from 400, 120
    
    def collect_bandwidth_data(self) -> Dict[str, float]:
        """Collect bandwidth usage from all active clients across all windows"""
        client_rates = {}
        
        try:
            # From Pointing Window
            if self.pointing_window:
                # GPS Widget
                if hasattr(self.pointing_window, 'gps_widget') and self.pointing_window.gps_widget.is_active:
                    rate = self.pointing_window.gps_widget.gps_client.get_data_rate_kbps()
                    if rate > 0:
                        client_rates['GPS (Pointing)'] = rate
                
                # Sky Chart Widget (uses OphClient)
                if (hasattr(self.pointing_window, 'sky_chart_widget') and 
                    self.pointing_window.sky_chart_widget.is_active):
                    rate = self.pointing_window.sky_chart_widget.oph_client.get_data_rate_kbps()
                    if rate > 0:
                        client_rates['Sky Chart Telemetry'] = rate
                
                # Star Camera Widget
                if (hasattr(self.pointing_window, 'star_camera_widget') and 
                    self.pointing_window.star_camera_widget.is_star_camera_active()):
                    # Star camera images
                    img_rate = self.pointing_window.star_camera_widget.get_data_rate_kbps()
                    if img_rate > 0:
                        client_rates['Star Camera Images'] = img_rate
                    
                    # Star camera telemetry (OphClient)
                    tel_rate = self.pointing_window.star_camera_widget.oph_client.get_data_rate_kbps()
                    if tel_rate > 0:
                        client_rates['Star Camera Telemetry'] = tel_rate
                
                # Motor Controller Widget
                if (hasattr(self.pointing_window, 'motor_controller_widget') and 
                    self.pointing_window.motor_controller_widget.is_motor_controller_active()):
                    rate = self.pointing_window.motor_controller_widget.oph_client.get_data_rate_kbps()
                    if rate > 0:
                        client_rates['Motor Controller'] = rate
                
                # Scanning Operations Widget
                if (hasattr(self.pointing_window, 'scanning_operations_widget') and 
                    self.pointing_window.scanning_operations_widget.is_active):
                    rate = self.pointing_window.scanning_operations_widget.oph_client.get_data_rate_kbps()
                    if rate > 0:
                        client_rates['Scanning Operations'] = rate
            
            # From Telescope Data Window
            if self.telescope_data_window:
                # Spectrometer Widget
                if (hasattr(self.telescope_data_window, 'spectra_widget') and 
                    self.telescope_data_window.spectra_widget.is_spectrometer_active()):
                    rate = self.telescope_data_window.spectra_widget.get_data_rate_kbps()
                    if rate > 0:
                        client_rates['BCP Spectrometer'] = rate
            
            # From Housekeeping Window
            if self.housekeeping_window:
                # PBoB Widget
                if (hasattr(self.housekeeping_window, 'pbob_widget') and 
                    self.housekeeping_window.pbob_widget.is_active):
                    rate = self.housekeeping_window.pbob_widget.oph_client.get_data_rate_kbps()
                    if rate > 0:
                        client_rates['PBoB Monitor'] = rate
                
                # PR59 Widget (doesn't have continuous data rate tracking, but uses bandwidth)
                if (hasattr(self.housekeeping_window, 'pr59_widget') and 
                    self.housekeeping_window.pr59_widget.is_active):
                    # PR59 requests are small and infrequent, estimate ~0.1 KB/s when active
                    client_rates['PR59 Controller'] = 0.1
                
                # Heater Widget (doesn't have continuous data rate tracking, but uses bandwidth)
                if (hasattr(self.housekeeping_window, 'heater_widget') and 
                    self.housekeeping_window.heater_widget.is_active):
                    # Heater requests are very small and infrequent, estimate ~0.05 KB/s when active
                    client_rates['Heater System'] = 0.05
                    
        except Exception as e:
            self.logger.error(f"Error collecting bandwidth data: {e}")
        
        return client_rates
    
    def update_bandwidth_display(self):
        """Update the bandwidth usage display"""
        try:
            # Collect current bandwidth usage
            self.client_rates = self.collect_bandwidth_data()
            self.current_total_kbps = sum(self.client_rates.values())
            
            # Update main display
            self.current_usage_label.setText(f"{self.current_total_kbps:.1f} KB/s")
            
            # Update color based on usage level
            usage_percentage = (self.current_total_kbps / self.bandwidth_limit_kbps) * 100
            
            # Update progress bar (scale percentage to 0-1000)
            progress_value = min(int(usage_percentage * 10), 1000)
            self.usage_progress.setValue(progress_value)
            
            # Update percentage label
            self.percentage_label.setText(f"{usage_percentage:.1f}%")
            if usage_percentage > 100:
                self.percentage_label.setStyleSheet("QLabel { color: #dc3545; border: none; background: transparent; font-weight: bold; }")
            else:
                self.percentage_label.setStyleSheet("QLabel { color: #6c757d; border: none; background: transparent; }")
            
            if usage_percentage > 90:
                color = "#dc3545"  # Red - danger
                self.usage_progress.setStyleSheet("""
                    QProgressBar { border: 1px solid #dee2e6; border-radius: 3px; background-color: #e9ecef; }
                    QProgressBar::chunk { background-color: #dc3545; border-radius: 2px; }
                """)
            elif usage_percentage > 75:
                color = "#ffc107"  # Yellow - warning
                self.usage_progress.setStyleSheet("""
                    QProgressBar { border: 1px solid #dee2e6; border-radius: 3px; background-color: #e9ecef; }
                    QProgressBar::chunk { background-color: #ffc107; border-radius: 2px; }
                """)
            else:
                color = "#28a745"  # Green - safe
                self.usage_progress.setStyleSheet("""
                    QProgressBar { border: 1px solid #dee2e6; border-radius: 3px; background-color: #e9ecef; }
                    QProgressBar::chunk { background-color: #28a745; border-radius: 2px; }
                """)
            
            self.current_usage_label.setStyleSheet(f"QLabel {{ color: {color}; border: none; background: transparent; }}")
            
            # Update top client label
            if self.client_rates:
                # Sort clients by bandwidth usage (highest first)
                sorted_clients = sorted(self.client_rates.items(), key=lambda x: x[1], reverse=True)
                top_client_name = sorted_clients[0][0]
                self.top_client_label.setText(f"Top Client: {top_client_name}")
            else:
                self.top_client_label.setText("No active clients")
            
        except Exception as e:
            self.logger.error(f"Error updating bandwidth display: {e}")
    
    def force_update(self):
        """Force an immediate update of the bandwidth display"""
        self.update_bandwidth_display()
    
    def get_current_usage(self) -> float:
        """Get current total bandwidth usage in KB/s"""
        return self.current_total_kbps
    
    def get_usage_percentage(self) -> float:
        """Get current usage as percentage of limit"""
        return (self.current_total_kbps / self.bandwidth_limit_kbps) * 100
    
    def is_over_limit(self) -> bool:
        """Check if current usage exceeds the bandwidth limit"""
        return self.current_total_kbps > self.bandwidth_limit_kbps
    
    def cleanup(self):
        """Clean up the network traffic widget"""
        try:
            # Stop the update timer
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
                
            self.logger.info("Network traffic widget cleaned up")
        except Exception as e:
            self.logger.error(f"Error during network traffic widget cleanup: {e}") 
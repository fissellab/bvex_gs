"""
Pointing Window for BVEX Ground Station
Contains sky chart, star camera, GPS display, and motor controller widgets
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout,
                             QWidget, QMenuBar, QStatusBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction
from src.gui.sky_chart_widget import SkyChartWidget
from src.gui.gps_display_widget import GPSDisplayWidget
from src.gui.star_camera_widget import StarCameraWidget
from src.gui.motor_controller_widget import MotorControllerWidget
from src.gui.scanning_operations_widget import ScanningOperationsWidget
from src.data.gps_client import GPSClient
from src.data.Oph_client import OphClient
from src.config.settings import GUI, GPS_SERVER, OPH_SERVER


class PointingWindow(QMainWindow):
    """Pointing window for telescope pointing operations"""
    
    def __init__(self, gps_client=None, shared_oph_client=None):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Use provided clients or create new ones
        self.gps_client = gps_client if gps_client else GPSClient()
        self.shared_oph_client = shared_oph_client if shared_oph_client else OphClient()
        self.owns_oph_client = shared_oph_client is None
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.setup_timers()
        
        # Start shared OphClient if we own it
        if self.owns_oph_client:
            if self.shared_oph_client.start():
                self.shared_oph_client.pause()  # Start paused
                self.logger.info("Shared OphClient started successfully (paused)")
            else:
                self.logger.error("Failed to start shared OphClient")
        
        # Auto-start GPS since the widget now starts active by default
        self.start_gps()
    
    def setup_ui(self):
        """Setup the pointing window UI layout"""
        self.setWindowTitle("BVEX Ground Station - Pointing")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: white; }")
        self.setCentralWidget(central_widget)
        
        # Main layout - two-column layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Left side - Sky chart and GPS + Motor Controller
        left_widget = QWidget()
        left_layout = QGridLayout()#left_widget
        left_widget.setLayout(left_layout)
        #left_layout.setContentsMargins(15, 0, 5, 0)
        #left_layout.setSpacing(15)  # Increased spacing
        
        # Sky chart widget (MUCH LARGER - this should be the dominant widget)
        self.sky_chart_widget = SkyChartWidget(oph_client=self.shared_oph_client)
        #self.sky_chart_widget.setGeometry(5,5,600,600)
        #self.sky_chart_widget.setMinimumSize(750, 500)  # Much larger - was 650x350
        #self.sky_chart_widget.setMaximumSize(900, 600)  # Much larger - was 750x400
        left_layout.addWidget(self.sky_chart_widget,0,0,3,3)  
        
        # GPS widget (compact - keep current good size)
        self.gps_widget = GPSDisplayWidget()
        #self.gps_widget.setMinimumHeight(220)  # Compact size
        #self.gps_widget.setMaximumHeight(250)  # Compact size
        left_layout.addWidget(self.gps_widget, 3,0,3,1)
        
        # Motor Controller widget (adequate space for information)
        self.motor_controller_widget = MotorControllerWidget(oph_client=self.shared_oph_client)
        #self.motor_controller_widget.setMinimumSize(450, 240)  # Keep good size for info
        #self.motor_controller_widget.setMaximumSize(500, 270)  # Keep good size for info
        left_layout.addWidget(self.motor_controller_widget,3,1,3,2) 
        # Remove the stretch to prevent squishing
        # left_layout.addStretch()
        
        # Right side - Star Camera and Scanning Operations (much larger now)
        right_widget = QWidget()
        right_layout = QGridLayout()
        right_widget.setLayout(right_layout)
        #right_layout.setContentsMargins(5, 0, 5, 0)
        #right_layout.setSpacing(10)
        
        self.star_camera_widget = StarCameraWidget(oph_client=self.shared_oph_client)
        #self.star_camera_widget.setMinimumSize(700, 600)  # Larger - information rich widget
        #self.star_camera_widget.setMaximumSize(800, 700)  # Larger - information rich widget  
        right_layout.addWidget(self.star_camera_widget, 0,0,3,3) 
        
        # Scanning Operations widget (below star camera - adequate space for info)
        self.scanning_operations_widget = ScanningOperationsWidget(oph_client=self.shared_oph_client)
        self.scanning_operations_widget.setMinimumSize(700, 200)  # Adequate size for info
        self.scanning_operations_widget.setMaximumSize(800, 240)  # Adequate size for info
        right_layout.addWidget(self.scanning_operations_widget, 3,0,2,3) 
        
        #right_layout.addStretch()
        
        # Add widgets to main layout
        main_layout.addWidget(left_widget, 1)  # Left side gets 1 part
        main_layout.addWidget(right_widget, 1)  # Right side gets 1 part
        
        # Set window properties - optimized for large sky chart and star camera
        self.setMinimumSize(1600, 1050)   # Increased to fit larger widgets properly
        self.resize(1800, 1150)           # Increased to fit larger widgets properly
    
    def setup_menu_bar(self):
        """Create pointing window menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Start/Stop GPS
        self.start_gps_action = QAction('&Start GPS', self)
        self.start_gps_action.triggered.connect(self.start_gps)
        file_menu.addAction(self.start_gps_action)
        
        self.stop_gps_action = QAction('&Stop GPS', self)
        self.stop_gps_action.triggered.connect(self.stop_gps)
        file_menu.addAction(self.stop_gps_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Refresh sky chart
        refresh_action = QAction('&Refresh Sky Chart', self)
        refresh_action.triggered.connect(lambda: self.sky_chart_widget.update_chart(0) if self.sky_chart_widget.is_sky_chart_active() else None)
        view_menu.addAction(refresh_action)
        
        # Star Camera menu
        star_camera_menu = menubar.addMenu('&Star Camera')
        
        # Force refresh image
        refresh_image_action = QAction('&Refresh Image', self)
        refresh_image_action.triggered.connect(lambda: self.star_camera_widget.request_image() if self.star_camera_widget.is_star_camera_active() else None)
        star_camera_menu.addAction(refresh_image_action)
        
        # Motor Controller menu
        motor_controller_menu = menubar.addMenu('&Motor Controller')
        
        # Force refresh motor controller telemetry
        refresh_motor_action = QAction('&Refresh Motor Telemetry', self)
        refresh_motor_action.triggered.connect(lambda: self.motor_controller_widget.update_telemetry() if self.motor_controller_widget.is_motor_controller_active() else None)
        motor_controller_menu.addAction(refresh_motor_action)
        
        # Scanning Operations menu
        scanning_menu = menubar.addMenu('&Scanning Operations')
        
        # Force refresh scanning telemetry
        refresh_scanning_action = QAction('&Refresh Scanning Telemetry', self)
        refresh_scanning_action.triggered.connect(lambda: self.scanning_operations_widget.update_telemetry() if self.scanning_operations_widget.is_scanning_operations_active() else None)
        scanning_menu.addAction(refresh_scanning_action)
    
    def setup_status_bar(self):
        """Create status bar for pointing window"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Pointing Window Ready", 3000)
    
    def setup_timers(self):
        """Setup update timers"""
        # GPS update timer
        self.gps_update_timer = QTimer()
        self.gps_update_timer.timeout.connect(self.update_gps_data)
        self.gps_update_timer.start(int(GPS_SERVER['update_interval'] * 1000))
        
        # Status update timer
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(GUI['update_interval'])
    
    def start_gps(self):
        """Start GPS client"""
        if self.gps_client.start():
            self.gps_client.resume()  # Resume data collection
            self.status_bar.showMessage("GPS started successfully", 3000)
            self.logger.info("GPS started")
        else:
            self.status_bar.showMessage("Failed to start GPS", 3000)
            self.logger.warning("GPS start failed")
    
    def stop_gps(self):
        """Stop GPS client"""
        self.gps_client.stop()
        self.status_bar.showMessage("GPS stopped", 3000)
        self.logger.info("GPS stopped")
    
    def update_gps_data(self):
        """Update GPS data from server"""
        # Only try to update GPS data if the client is running and not paused
        if hasattr(self, 'gps_client') and self.gps_client.running and not self.gps_client.is_paused():
            try:
                gps_data = self.gps_client.get_gps_data()
                if gps_data and gps_data.valid:
                    # Update GPS display
                    self.gps_widget.update_gps_data(gps_data, self.gps_client)
                    
                    # Update sky chart with GPS data
                    self.sky_chart_widget.set_gps_data(gps_data)
                    
            except Exception as e:
                self.logger.error(f"Error updating GPS data: {e}")
        # If GPS is not running, just skip silently (no warnings)
    
    def update_status(self):
        """Update status information"""
        try:
            # Update sky chart with star camera data if available
            if self.shared_oph_client.is_connected():
                oph_data = self.shared_oph_client.get_data()
                if oph_data.valid:
                    self.sky_chart_widget.set_star_camera_data(oph_data)
                    
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Pointing window shutting down...")
        
        # Stop timers
        if hasattr(self, 'gps_update_timer'):
            self.gps_update_timer.stop()
        if hasattr(self, 'status_update_timer'):
            self.status_update_timer.stop()
        
        # Cleanup components
        try:
            # GPS cleanup
            if hasattr(self, 'gps_client'):
                self.gps_client.cleanup()
            
            # Star camera widget cleanup
            if hasattr(self, 'star_camera_widget'):
                self.star_camera_widget.stop_star_camera()
                if hasattr(self.star_camera_widget, 'worker_thread'):
                    self.star_camera_widget.worker_thread.quit()
                    self.star_camera_widget.worker_thread.wait()
            
            # Motor controller widget cleanup
            if hasattr(self, 'motor_controller_widget'):
                self.motor_controller_widget.stop_motor_controller()
            
            # Scanning operations widget cleanup
            if hasattr(self, 'scanning_operations_widget'):
                self.scanning_operations_widget.stop_scanning_operations()
            
            # Cleanup shared Oph client only if we own it
            if self.owns_oph_client and hasattr(self, 'shared_oph_client'):
                self.shared_oph_client.cleanup()
            
            # Sky chart cleanup
            if hasattr(self, 'sky_chart_widget') and self.sky_chart_widget.is_sky_chart_active():
                self.sky_chart_widget.stop_animation()
            
            self.logger.info("Pointing window cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during pointing window cleanup: {e}")
        
        event.accept() 

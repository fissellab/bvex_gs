"""
Pointing Window for BVEX Ground Station
Contains sky chart, star camera, GPS display, and motor controller widgets
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout,
                             QWidget, QMenuBar, QStatusBar, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction
from src.gui.sky_chart_widget import SkyChartWidget
from src.gui.gps_display_widget import GPSDisplayWidget
from src.gui.star_camera_widget import StarCameraWidget
from src.gui.motor_controller_widget import MotorControllerWidget
from src.gui.scanning_operations_widget import ScanningOperationsWidget
# GPS client removed - GPS widget manages its own client
from src.data.Oph_client import OphClient
from src.config.settings import GUI, GPS_SERVER, OPH_SERVER


class PointingWindow(QMainWindow):
    """Pointing window for telescope pointing operations"""
    
    def __init__(self, gps_client=None, shared_oph_client=None):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # GPS widget now manages its own client
        # No need for window-level GPS management
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.setup_timers()
    
    def get_safe_window_size(self, width_percentage=0.75, height_percentage=0.75):
        """Get a safe window size that won't be cut off on any reasonable monitor"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()  # Excludes taskbars, etc.
            width = int(geometry.width() * width_percentage)
            height = int(geometry.height() * height_percentage)
            return width, height
        else:
            # Fallback for safety
            return 1200, 800
    
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
        self.sky_chart_widget = SkyChartWidget()
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
        self.motor_controller_widget = MotorControllerWidget()
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
        
        self.star_camera_widget = StarCameraWidget()
        #self.star_camera_widget.setMinimumSize(700, 600)  # Larger - information rich widget
        #self.star_camera_widget.setMaximumSize(800, 700)  # Larger - information rich widget  
        right_layout.addWidget(self.star_camera_widget, 0,0,3,3) 
        
        # Scanning Operations widget (below star camera - adequate space for info)
        self.scanning_operations_widget = ScanningOperationsWidget()
        self.scanning_operations_widget.setMinimumSize(700, 200)  # Adequate size for info
        self.scanning_operations_widget.setMaximumSize(800, 240)  # Adequate size for info
        right_layout.addWidget(self.scanning_operations_widget, 3,0,2,3) 
        
        #right_layout.addStretch()
        
        # Add widgets to main layout
        main_layout.addWidget(left_widget, 1)  # Left side gets 1 part
        main_layout.addWidget(right_widget, 1)  # Right side gets 1 part
        
        # Set window properties - adaptive sizing for multi-monitor setups
        width, height = self.get_safe_window_size(0.80, 0.75)  # 80% width, 75% height
        self.setMinimumSize(max(1200, width//2), max(800, height//2))  # Reasonable minimum
        self.resize(width, height)
    
    def setup_menu_bar(self):
        """Create pointing window menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Start/Stop GPS
        # GPS menu items removed - GPS widget manages its own state
        
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
        # Status update timer
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(GUI['update_interval'])
    
    # GPS methods removed - GPS widget manages its own client
    
    def update_status(self):
        """Update status information"""
        try:
            # Widgets now manage their own data access and updates
            pass
                    
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Pointing window shutting down...")
        
        # Stop timers
        if hasattr(self, 'status_update_timer'):
            self.status_update_timer.stop()
        
        # Cleanup components
        try:
            # Widgets now manage their own clients
            
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
                    # Widgets now manage their own OphClients
            
            # Sky chart cleanup
            if hasattr(self, 'sky_chart_widget') and self.sky_chart_widget.is_sky_chart_active():
                self.sky_chart_widget.stop_animation()
            
            self.logger.info("Pointing window cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during pointing window cleanup: {e}")
        
        event.accept() 

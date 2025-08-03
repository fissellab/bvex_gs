"""
Telescope Data Window for BVEX Ground Station
Contains spectrometer and other scientific instrument widgets
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, 
                             QWidget, QMenuBar, QStatusBar, QGridLayout, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction

from src.gui.spectra_display_widget import SpectraDisplayWidget
from src.gui.vlbi_telemetry_widget import VLBITelemetryWidget
from src.config.settings import GUI


class TelescopeDataWindow(QMainWindow):
    """Telescope data window for scientific data visualization"""
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
    
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
        """Setup the telescope data window UI layout"""
        self.setWindowTitle("BVEX Ground Station - Telescope Data")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: white; }")
        self.setCentralWidget(central_widget)
        
        # Use QGridLayout: 1 row, 2 columns (spectrometer on left, VLBI on right)
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Spectra display widget - Row 0, Column 0 (left side, larger)
        self.spectra_widget = SpectraDisplayWidget()
        self.spectra_widget.setMinimumSize(900, 600)  # Reduced from 1200x800 to make room for VLBI
        self.spectra_widget.setMaximumSize(1200, 800)  # Reduced from 1600x1000
        
        main_layout.addWidget(self.spectra_widget, 0, 0)
        
        # VLBI telemetry widget - Row 0, Column 1 (right side, smaller)
        self.vlbi_widget = VLBITelemetryWidget()
        self.vlbi_widget.setMinimumSize(400, 300)
        self.vlbi_widget.setMaximumSize(500, 400)
        
        main_layout.addWidget(self.vlbi_widget, 0, 1, Qt.AlignmentFlag.AlignTop)
        
        # Set column stretch factors (spectrometer gets more space)
        main_layout.setColumnStretch(0, 3)  # Spectrometer: 75% width
        main_layout.setColumnStretch(1, 1)  # VLBI: 25% width
        
        # Set window properties - adaptive sizing for multi-monitor setups
        width, height = self.get_safe_window_size(0.85, 0.70)  # Increased width to 85% for both widgets
        self.setMinimumSize(max(1300, width//2), max(700, height//2))  # Increased minimum width
        self.resize(width, height)
    
    def setup_menu_bar(self):
        """Create telescope data window menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Spectrometer menu
        spectrometer_menu = menubar.addMenu('&Spectrometer')
        
        # Force refresh spectra
        refresh_spectra_action = QAction('&Refresh Spectra', self)
        refresh_spectra_action.triggered.connect(lambda: self.spectra_widget.trigger_fetch() if self.spectra_widget.is_spectrometer_active() else None)
        spectrometer_menu.addAction(refresh_spectra_action)
        
        # VLBI menu
        vlbi_menu = menubar.addMenu('&VLBI')
        
        # Start/Stop VLBI monitoring
        toggle_vlbi_action = QAction('&Toggle VLBI Monitor', self)
        toggle_vlbi_action.triggered.connect(lambda: self.vlbi_widget.toggle_state())
        vlbi_menu.addAction(toggle_vlbi_action)
        
        # Force refresh VLBI data
        refresh_vlbi_action = QAction('&Refresh VLBI Data', self)
        refresh_vlbi_action.triggered.connect(lambda: self.vlbi_widget.trigger_fetch() if self.vlbi_widget.is_vlbi_active() else None)
        vlbi_menu.addAction(refresh_vlbi_action)
    
    def setup_status_bar(self):
        """Create status bar for telescope data window"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Telescope Data Window Ready", 3000)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Telescope data window shutting down...")
        
        # Cleanup components
        try:
            # Spectra widget cleanup
            if hasattr(self, 'spectra_widget'):
                self.spectra_widget.cleanup()
            
            # VLBI widget cleanup
            if hasattr(self, 'vlbi_widget'):
                self.vlbi_widget.cleanup()
            
            self.logger.info("Telescope data window cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during telescope data window cleanup: {e}")
        
        event.accept() 
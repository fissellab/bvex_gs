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
from src.gui.ticc_widget import TICCWidget
from src.gui.backend_status_widget import BackendStatusWidget
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
        
        # Use QGridLayout: 3 rows, 2 columns (spectrometer on left, VLBI/Backend/TICC on right)
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Spectra display widget - Row 0-2, Column 0 (left side, spans 3 rows, larger)
        self.spectra_widget = SpectraDisplayWidget()
        self.spectra_widget.setMinimumSize(900, 600)  # Reduced from 1200x800 to make room for all widgets
        self.spectra_widget.setMaximumSize(1200, 800)  # Reduced from 1600x1000
        
        main_layout.addWidget(self.spectra_widget, 0, 0, 3, 1)  # Span 3 rows
        
        # VLBI telemetry widget - Row 0, Column 1 (top right)
        self.vlbi_widget = VLBITelemetryWidget()
        self.vlbi_widget.setMinimumSize(400, 280)  # Reduced height to fit 3 widgets
        self.vlbi_widget.setMaximumSize(500, 350)  # Reduced height to fit 3 widgets
        
        main_layout.addWidget(self.vlbi_widget, 0, 1, Qt.AlignmentFlag.AlignTop)
        
        # Backend status widget - Row 1, Column 1 (middle right, between VLBI and TICC)
        self.backend_widget = BackendStatusWidget()
        self.backend_widget.setMinimumSize(400, 280)  # Same footprint as others
        self.backend_widget.setMaximumSize(500, 350)  # Same footprint as others
        
        main_layout.addWidget(self.backend_widget, 1, 1, Qt.AlignmentFlag.AlignTop)
        
        # TICC widget - Row 2, Column 1 (bottom right, below backend)
        self.ticc_widget = TICCWidget()
        self.ticc_widget.setMinimumSize(400, 280)  # Reduced height to fit 3 widgets
        self.ticc_widget.setMaximumSize(500, 350)  # Reduced height to fit 3 widgets
        
        main_layout.addWidget(self.ticc_widget, 2, 1, Qt.AlignmentFlag.AlignTop)
        
        # Set column stretch factors (spectrometer gets more space)
        main_layout.setColumnStretch(0, 3)  # Spectrometer: 75% width
        main_layout.setColumnStretch(1, 1)  # VLBI + Backend + TICC: 25% width
        
        # Set row stretch factors to distribute space evenly between the 3 right widgets
        main_layout.setRowStretch(0, 1)  # VLBI row
        main_layout.setRowStretch(1, 1)  # Backend row
        main_layout.setRowStretch(2, 1)  # TICC row
        
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
        
        # Backend menu
        backend_menu = menubar.addMenu('&Backend')
        
        # Start/Stop Backend monitoring
        toggle_backend_action = QAction('&Toggle Backend Monitor', self)
        toggle_backend_action.triggered.connect(lambda: self.backend_widget.toggle_state())
        backend_menu.addAction(toggle_backend_action)
        
        # Force refresh Backend data
        refresh_backend_action = QAction('&Refresh Backend Data', self)
        refresh_backend_action.triggered.connect(lambda: self.backend_widget.trigger_fetch() if self.backend_widget.is_backend_active() else None)
        backend_menu.addAction(refresh_backend_action)
        
        # TICC menu
        ticc_menu = menubar.addMenu('&TICC')
        
        # Start/Stop TICC monitoring
        toggle_ticc_action = QAction('&Toggle TICC Monitor', self)
        toggle_ticc_action.triggered.connect(lambda: self.ticc_widget.toggle_state())
        ticc_menu.addAction(toggle_ticc_action)
        
        # Force refresh TICC data
        refresh_ticc_action = QAction('&Refresh TICC Data', self)
        refresh_ticc_action.triggered.connect(lambda: self.ticc_widget.trigger_fetch() if self.ticc_widget.is_ticc_active() else None)
        ticc_menu.addAction(refresh_ticc_action)
    
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
            
            # Backend widget cleanup
            if hasattr(self, 'backend_widget'):
                self.backend_widget.cleanup()
            
            # TICC widget cleanup
            if hasattr(self, 'ticc_widget'):
                self.ticc_widget.cleanup()
            
            self.logger.info("Telescope data window cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during telescope data window cleanup: {e}")
        
        event.accept() 
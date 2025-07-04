"""
Housekeeping Window for BVEX Ground Station
Contains data logging controls and other housekeeping/monitoring widgets
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QMenuBar, QStatusBar, QFrame, QPushButton, QLabel, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction

from src.data.data_logger import DataLogger
from src.config.settings import GUI
from src.gui.pbob_widget import PBoBWidget


class HousekeepingWindow(QMainWindow):
    """Housekeeping window for system monitoring and control"""
    
    def __init__(self, pointing_window=None, telescope_data_window=None, shared_oph_client=None):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # References to other windows for data logger access
        self.pointing_window = pointing_window
        self.telescope_data_window = telescope_data_window
        
        # Data logger will be initialized after UI setup
        self.data_logger = None
        
        # The PBoB widget will handle its own connection to the shared manager
        # No need to manage the Oph client directly in this window
        self.logger.info("Housekeeping window initialized - widgets will use shared Oph client manager")
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        
        # Setup data logger after UI is ready
        self.setup_data_logger()
    
    def setup_ui(self):
        """Setup the housekeeping window UI layout"""
        self.setWindowTitle("BVEX Ground Station - Housekeeping")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: white; }")
        self.setCentralWidget(central_widget)
        
        # Use QGridLayout: 3 rows, 2 columns (Data Logging | PBoB | Stretch)
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Data logging panel (compact) - Row 0, Column 0 (left-aligned)
        self.setup_compact_data_logging_panel_grid(main_layout)
        
        # PBoB (Power Distribution Box) Widget - Row 1, Column 0 (left-aligned)
        self.pbob_widget = PBoBWidget(parent=self, oph_client=None)
        main_layout.addWidget(self.pbob_widget, 1, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        # Set column stretch to allow horizontal expansion (empty column 1 stretches)
        main_layout.setColumnStretch(1, 1)
        
        # Set row stretch to push widgets to top (row 2 stretches)
        main_layout.setRowStretch(2, 1)
        
        # Set window properties
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
    
    def setup_compact_data_logging_panel_grid(self, main_layout):
        """Setup the compact data logging control panel for grid layout"""
        # Create compact data logging panel frame
        data_logging_frame = QFrame()
        data_logging_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        data_logging_frame.setMinimumHeight(100)
        data_logging_frame.setMaximumHeight(120)
        data_logging_frame.setMinimumWidth(280)
        data_logging_frame.setMaximumWidth(320)
        data_logging_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        # Layout for the data logging panel
        panel_layout = QVBoxLayout(data_logging_frame)
        panel_layout.setContentsMargins(10, 8, 10, 8)
        panel_layout.setSpacing(6)
        
        # Title label
        title_label = QLabel("📊 Data Logging")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("QLabel { color: #495057; border: none; margin: 0px; }")
        panel_layout.addWidget(title_label)
        
        # Button and status layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Toggle button
        self.data_logging_toggle_button = QPushButton("Start Logging")
        self.data_logging_toggle_button.setMinimumHeight(35)
        self.data_logging_toggle_button.setMinimumWidth(110)
        self.data_logging_toggle_button.clicked.connect(self.toggle_data_logging)
        self.data_logging_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        # Status label
        self.data_logging_status_text = QLabel("Stopped")
        self.data_logging_status_text.setFont(QFont("Arial", 10))
        self.data_logging_status_text.setStyleSheet("QLabel { color: #6c757d; border: none; margin: 0px; }")
        
        button_layout.addWidget(self.data_logging_toggle_button)
        button_layout.addWidget(self.data_logging_status_text)
        
        panel_layout.addLayout(button_layout)
        
        # File info label (compact)
        self.data_logging_file_label = QLabel("No log file")
        self.data_logging_file_label.setFont(QFont("Arial", 9))
        self.data_logging_file_label.setStyleSheet("QLabel { color: #868e96; border: none; margin: 0px; }")
        panel_layout.addWidget(self.data_logging_file_label)
        
        # Add the panel to the grid layout - Row 0, Column 0 (left-aligned)
        main_layout.addWidget(data_logging_frame, 0, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    
    def setup_data_logger(self):
        """Setup the comprehensive data logger (adapted from main_window.py)"""
        try:
            # Initialize data logger with reference to this housekeeping window
            self.data_logger = DataLogger(main_window=self)
            self.logger.info("Data logger initialized successfully - using GUI widget data sources")
        except Exception as e:
            self.logger.error(f"Failed to initialize data logger: {e}")
            self.data_logger = None
    
    def setup_menu_bar(self):
        """Create housekeeping window menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Data Logging menu
        logging_menu = menubar.addMenu('&Data Logging')
        
        # Toggle data logging action
        self.toggle_logging_action = QAction('&Start Data Logging', self)
        self.toggle_logging_action.triggered.connect(self.toggle_data_logging)
        self.toggle_logging_action.setCheckable(True)
        logging_menu.addAction(self.toggle_logging_action)
        
        # Show log file location action
        show_log_file_action = QAction('&Show Log File Location', self)
        show_log_file_action.triggered.connect(self.show_log_file_location)
        logging_menu.addAction(show_log_file_action)
    
    def setup_status_bar(self):
        """Create status bar for housekeeping window"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Housekeeping Window Ready", 3000)
    
    def toggle_data_logging(self):
        """Toggle data logging on/off (adapted from main_window.py)"""
        if not self.data_logger:
            QMessageBox.warning(
                self, 
                "Data Logger Error", 
                "Data logger is not initialized. Please restart the application."
            )
            return
        
        try:
            if self.data_logger.is_active():
                # Stop logging
                self.data_logger.stop_logging()
                self.update_data_logging_ui(False)
                self.status_bar.showMessage("Data logging stopped", 3000)
                self.logger.info("Data logging stopped by user")
            else:
                # Start or resume logging
                if self.data_logger.get_log_file_path():
                    # Resume existing log
                    if self.data_logger.resume_logging():
                        self.update_data_logging_ui(True)
                        self.status_bar.showMessage("Data logging resumed", 3000)
                        self.logger.info("Data logging resumed by user")
                    else:
                        QMessageBox.warning(
                            self, 
                            "Data Logging Error", 
                            "Failed to resume data logging. Check the logs for details."
                        )
                else:
                    # Start new log
                    if self.data_logger.start_logging():
                        self.update_data_logging_ui(True)
                        self.status_bar.showMessage("Data logging started", 3000)
                        self.logger.info("Data logging started by user")
                    else:
                        QMessageBox.warning(
                            self, 
                            "Data Logging Error", 
                            "Failed to start data logging. Check the logs for details."
                        )
        except Exception as e:
            self.logger.error(f"Error toggling data logging: {e}")
            QMessageBox.critical(
                self, 
                "Data Logging Error", 
                f"An error occurred while toggling data logging:\n{str(e)}"
            )
    
    def update_data_logging_ui(self, is_active: bool):
        """Update both menu and visible UI elements for data logging state (adapted from main_window.py)"""
        if is_active:
            # Update menu action
            self.toggle_logging_action.setText('&Stop Data Logging')
            self.toggle_logging_action.setChecked(True)
            
            # Update visible button
            if hasattr(self, 'data_logging_toggle_button'):
                self.data_logging_toggle_button.setText("Stop Logging")
                self.data_logging_toggle_button.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                    QPushButton:pressed {
                        background-color: #bd2130;
                    }
                """)
                
            # Update status text
            if hasattr(self, 'data_logging_status_text'):
                self.data_logging_status_text.setText("Active")
                self.data_logging_status_text.setStyleSheet("QLabel { color: #28a745; border: none; margin: 0px; font-weight: bold; }")
                
            # Update file label
            if hasattr(self, 'data_logging_file_label') and self.data_logger:
                log_file = self.data_logger.get_log_file_path()
                if log_file:
                    filename = os.path.basename(log_file)
                    # Truncate filename if too long
                    if len(filename) > 20:
                        filename = filename[:17] + "..."
                    self.data_logging_file_label.setText(f"{filename}")
        else:
            # Update menu action
            self.toggle_logging_action.setText('&Start Data Logging')
            self.toggle_logging_action.setChecked(False)
            
            # Update visible button
            if hasattr(self, 'data_logging_toggle_button'):
                self.data_logging_toggle_button.setText("Start Logging")
                self.data_logging_toggle_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                    QPushButton:pressed {
                        background-color: #1e7e34;
                    }
                """)
                
            # Update status text
            if hasattr(self, 'data_logging_status_text'):
                self.data_logging_status_text.setText("Stopped")
                self.data_logging_status_text.setStyleSheet("QLabel { color: #6c757d; border: none; margin: 0px; }")
                
            # Update file label
            if hasattr(self, 'data_logging_file_label'):
                self.data_logging_file_label.setText("No log file")
    
    def show_log_file_location(self):
        """Show the current log file location (adapted from main_window.py)"""
        if not self.data_logger:
            QMessageBox.information(
                self, 
                "Data Logger", 
                "Data logger is not initialized."
            )
            return
        
        log_file = self.data_logger.get_log_file_path()
        if log_file:
            log_dir = os.path.dirname(log_file)
            log_filename = os.path.basename(log_file)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Data Log File Location")
            msg.setText(f"Current log file:\n{log_filename}")
            msg.setDetailedText(f"Full path:\n{log_file}\n\nDirectory:\n{log_dir}")
            msg.exec()
        else:
            QMessageBox.information(
                self, 
                "Data Log File Location", 
                "No active log file. Start data logging to create a new log file."
            )
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Housekeeping window shutting down...")
        
        # Cleanup components
        try:
            # Data logger cleanup
            if hasattr(self, 'data_logger') and self.data_logger:
                self.data_logger.stop_logging()
                self.logger.info("Data logging stopped during shutdown")
            
            # PBoB widget cleanup
            if hasattr(self, 'pbob_widget') and self.pbob_widget:
                self.pbob_widget.cleanup()
                self.logger.info("PBoB widget cleaned up during shutdown")
            
            # The PBOB widget handles its own unregistration from shared manager
            # No need to manage the shared Oph client directly
            
            self.logger.info("Housekeeping window cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during housekeeping window cleanup: {e}")
        
        event.accept() 
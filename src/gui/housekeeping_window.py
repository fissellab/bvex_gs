"""
Housekeeping Window for BVEX Ground Station
Contains data logging controls and other housekeeping/monitoring widgets
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QMenuBar, QStatusBar, QFrame, QPushButton, QLabel, QMessageBox, QGridLayout, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction

from src.data.data_logging_orchestrator import DataLoggingOrchestrator
from src.config.settings import GUI, PR59_SERVER, HEATER_SERVER
from src.gui.pbob_widget import PBoBWidget
from src.gui.pr59_widget import PR59Widget
from src.gui.heater_widget import HeaterWidget
from src.gui.network_traffic_widget import NetworkTrafficWidget


class HousekeepingWindow(QMainWindow):
    """Housekeeping window for system monitoring and control"""
    
    def __init__(self, pointing_window=None, telescope_data_window=None, shared_oph_client=None):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # References to other windows for data logger access
        self.pointing_window = pointing_window
        self.telescope_data_window = telescope_data_window
        
        # Data logging orchestrator will be initialized after UI setup
        self.data_logging_orchestrator = None
        
        # Widgets now manage their own independent OphClients
        self.logger.info("Housekeeping window initialized - widgets use independent OphClients")
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        
        # Setup data logger after UI is ready
        self.setup_data_logger()
    
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
        """Setup the housekeeping window UI layout"""
        self.setWindowTitle("BVEX Ground Station - Housekeeping")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: white; }")
        self.setCentralWidget(central_widget)
        
        # Use QGridLayout: 3 rows, 2 columns (Data Logging + Network Traffic spans both | PBoB left, Heater right | PR59 left, empty right)
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Row 0: Data logging panel and Network Traffic Monitor side by side
        self.setup_top_control_panels(main_layout)
        
        # PBoB (Power Distribution Box) Widget - Row 1, Column 0 (left side)
        self.pbob_widget = PBoBWidget(parent=self, oph_client=None)
        main_layout.addWidget(self.pbob_widget, 1, 0,3,2,alignment=Qt.AlignmentFlag.AlignTop)
        
        # Heater System Widget - Row 1, Column 1 (right side, beside PBoB)
        self.heater_widget = HeaterWidget(
            parent=self,
            server_ip=HEATER_SERVER['host'],
            server_port=HEATER_SERVER['port']
        )
        main_layout.addWidget(self.heater_widget, 0, 2,2,2,alignment=Qt.AlignmentFlag.AlignTop)
        
        # PR59 Temperature Controller Widget - Row 2, Column 0 (left side, undisturbed)
        self.pr59_widget = PR59Widget(
            parent=self, 
            server_ip=PR59_SERVER['host'], 
            server_port=PR59_SERVER['port']
        )
        main_layout.addWidget(self.pr59_widget, 2, 2,2,2,alignment=Qt.AlignmentFlag.AlignTop)
        
        # Set column stretch to distribute space evenly between columns
        #main_layout.setColumnStretch(0, 1)  # Left column gets equal space
        #main_layout.setColumnStretch(1, 1)  # Right column gets equal space
        
        # Set row stretch to push widgets to top (row 3 stretches)
        #main_layout.setRowStretch(3, 1)
        
        # Set window properties - adaptive sizing for multi-monitor setups
        width, height = self.get_safe_window_size(0.75, 0.65)  # 75% width, 65% height for housekeeping
        self.setMinimumSize(max(1100, width//2), max(600, height//2))  # Reasonable minimum
        self.resize(width, height)
            
    def setup_top_control_panels(self, main_layout):
        """Setup the top row with data logging and network traffic panels"""
        # Create container for top control panels
        #top_controls_widget = QWidget()
        #top_controls_layout = QHBoxLayout(top_controls_widget)
        #top_controls_layout.setContentsMargins(0, 0, 0, 0)
        #top_controls_layout.setSpacing(15)
        
        # Data logging panel (left side)
        self.setup_compact_data_logging_panel_standalone()
        main_layout.addWidget(self.data_logging_panel,0,0,1,1)
        
        # Network Traffic Monitor (right side)
        self.network_traffic_widget = NetworkTrafficWidget(
            parent=self,
            pointing_window=self.pointing_window,
            telescope_data_window=self.telescope_data_window,
            housekeeping_window=self
        )
        main_layout.addWidget(self.network_traffic_widget,0,1,1,1)
    
    def setup_compact_data_logging_panel_standalone(self):
        """Setup the compact data logging control panel as a standalone widget"""
        # Create compact data logging panel frame
        self.data_logging_panel = QFrame()
        self.data_logging_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        self.data_logging_panel.setMinimumHeight(100)
        self.data_logging_panel.setMaximumHeight(120)
        self.data_logging_panel.setMinimumWidth(280)
        self.data_logging_panel.setMaximumWidth(320)
        self.data_logging_panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        # Layout for the data logging panel
        panel_layout = QVBoxLayout(self.data_logging_panel)
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
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        # Status label
        self.data_logging_status_label = QLabel("Status: Ready")
        self.data_logging_status_label.setFont(QFont("Arial", 9))
        self.data_logging_status_label.setStyleSheet("QLabel { color: #6c757d; border: none; }")
        
        button_layout.addWidget(self.data_logging_toggle_button)
        button_layout.addWidget(self.data_logging_status_label)
        panel_layout.addLayout(button_layout)
        
        # File info label (compact)
        self.data_logging_file_label = QLabel("No log file")
        self.data_logging_file_label.setFont(QFont("Arial", 9))
        self.data_logging_file_label.setStyleSheet("QLabel { color: #868e96; border: none; margin: 0px; }")
        panel_layout.addWidget(self.data_logging_file_label)
    
    def setup_data_logger(self):
        """Setup the new data logging orchestrator"""
        try:
            from src.data.loggers.gps_logger import GPSDataLogger
            from src.data.loggers.spectrometer_logger import SpectrometerDataLogger
            from src.data.loggers.star_camera_logger import StarCameraDataLogger
            from src.data.loggers.motor_controller_logger import MotorControllerDataLogger
            from src.data.loggers.pr59_logger import PR59DataLogger
            from src.data.loggers.heater_logger import HeaterDataLogger
            from src.data.loggers.ophiuchus_logger import OphiuchusDataLogger

            # Initialize orchestrator
            self.data_logging_orchestrator = DataLoggingOrchestrator()
            
            # Register loggers for available widgets
            if self.pointing_window:
                if hasattr(self.pointing_window, 'gps_display_widget'):
                    gps_logger = GPSDataLogger(
                        self.data_logging_orchestrator.session_manager,
                        self.pointing_window.gps_display_widget
                    )
                    self.data_logging_orchestrator.register_logger('gps', gps_logger)
                
                if hasattr(self.pointing_window, 'star_camera_widget'):
                    star_camera_logger = StarCameraDataLogger(
                        self.data_logging_orchestrator.session_manager,
                        self.pointing_window.star_camera_widget
                    )
                    self.data_logging_orchestrator.register_logger('star_camera', star_camera_logger)
                    self.data_logging_orchestrator.register_image_logger(
                        'star_camera', star_camera_logger.image_logger
                    )
                
                if hasattr(self.pointing_window, 'motor_controller_widget'):
                    motor_logger = MotorControllerDataLogger(
                        self.data_logging_orchestrator.session_manager,
                        self.pointing_window.motor_controller_widget
                    )
                    self.data_logging_orchestrator.register_logger('motor_controller', motor_logger)
                
                if hasattr(self.pointing_window, 'scanning_operations_widget'):
                    scanning_logger = OphiuchusDataLogger(
                        self.data_logging_orchestrator.session_manager,
                        self.pointing_window.scanning_operations_widget
                    )
                    self.data_logging_orchestrator.register_logger('ophiuchus_scanning', scanning_logger)
            
            if self.telescope_data_window:
                if hasattr(self.telescope_data_window, 'spectra_widget'):
                    spectrometer_logger = SpectrometerDataLogger(
                        self.data_logging_orchestrator.session_manager,
                        self.telescope_data_window.spectra_widget
                    )
                    self.data_logging_orchestrator.register_logger('spectrometer', spectrometer_logger)
            
            # Register household loggers
            pr59_logger = PR59DataLogger(
                self.data_logging_orchestrator.session_manager,
                self.pr59_widget
            )
            self.data_logging_orchestrator.register_logger('pr59_temperature', pr59_logger)
            
            heater_logger = HeaterDataLogger(
                self.data_logging_orchestrator.session_manager,
                self.heater_widget
            )
            self.data_logging_orchestrator.register_logger('heater_system', heater_logger)
            
            # Register PBoB logger
            from src.data.loggers.pbob_logger import PBoBDataLogger
            pbob_logger = PBoBDataLogger(
                self.data_logging_orchestrator.session_manager,
                self.pbob_widget
            )
            self.data_logging_orchestrator.register_logger('pbob', pbob_logger)
            
            self.logger.info("Data logging orchestrator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize data logging orchestrator: {e}")
            self.data_logging_orchestrator = None
    
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
        """Toggle data logging on/off using new orchestrator"""
        if not self.data_logging_orchestrator:
            QMessageBox.warning(
                self, 
                "Data Logging Error", 
                "Data logging orchestrator is not initialized. Please restart the application."
            )
            return
        
        try:
            if self.data_logging_orchestrator.is_logging_active():
                # Stop logging
                success = self.data_logging_orchestrator.stop_logging()
                if success:
                    self.update_data_logging_ui(False)
                    self.status_bar.showMessage("Data logging stopped", 3000)
                    self.logger.info("Data logging stopped by user")
                else:
                    QMessageBox.warning(
                        self, 
                        "Data Logging Error", 
                        "Failed to stop data logging. Check the logs for details."
                    )
            else:
                # Start new session
                success = self.data_logging_orchestrator.start_logging()
                if success:
                    self.update_data_logging_ui(True)
                    session_path = self.data_logging_orchestrator.get_session_path()
                    self.status_bar.showMessage(f"Data logging started: {session_path}", 3000)
                    self.logger.info(f"Data logging started by user: {session_path}")
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
            if hasattr(self, 'data_logging_status_label'):
                self.data_logging_status_label.setText("Status: Active")
                self.data_logging_status_label.setStyleSheet("QLabel { color: #28a745; border: none; margin: 0px; font-weight: bold; }")
                
            # Update file label
            if hasattr(self, 'data_logging_file_label') and self.data_logging_orchestrator:
                session_path = self.data_logging_orchestrator.get_session_path()
                if session_path:
                    session_name = os.path.basename(session_path)
                    # Truncate filename if too long
                    if len(session_name) > 20:
                        session_name = session_name[:17] + "..."
                    self.data_logging_file_label.setText(f"{session_name}")
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
            if hasattr(self, 'data_logging_status_label'):
                self.data_logging_status_label.setText("Status: Stopped")
                self.data_logging_status_label.setStyleSheet("QLabel { color: #6c757d; border: none; margin: 0px; }")
                
            # Update file label
            if hasattr(self, 'data_logging_file_label'):
                self.data_logging_file_label.setText("No log file")
    
    def show_log_file_location(self):
        """Show the current session location"""
        if not self.data_logging_orchestrator:
            QMessageBox.information(
                self, 
                "Data Logger", 
                "Data logging orchestrator is not initialized."
            )
            return
        
        session_path = self.data_logging_orchestrator.get_session_path()
        if session_path:
            session_name = os.path.basename(session_path)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Data Log Session Location")
            msg.setText(f"Current session:\n{session_name}")
            msg.setDetailedText(f"Full path:\n{session_path}")
            msg.exec()
        else:
            QMessageBox.information(
                self, 
                "Data Log File Location", 
                "No active session. Start data logging to create a new session."
            )
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Housekeeping window shutting down...")
        
        # Cleanup components
        try:
            # Data logger cleanup
            if hasattr(self, 'data_logging_orchestrator') and self.data_logging_orchestrator:
                self.data_logging_orchestrator.stop_logging()
                self.logger.info("Data logging stopped during shutdown")
            
            # PBoB widget cleanup
            if hasattr(self, 'pbob_widget') and self.pbob_widget:
                self.pbob_widget.cleanup()
                self.logger.info("PBoB widget cleaned up during shutdown")
            
            # PR59 widget cleanup
            if hasattr(self, 'pr59_widget') and self.pr59_widget:
                self.pr59_widget.cleanup()
                self.logger.info("PR59 widget cleaned up during shutdown")
            
            # Heater widget cleanup
            if hasattr(self, 'heater_widget') and self.heater_widget:
                self.heater_widget.cleanup()
                self.logger.info("Heater widget cleaned up during shutdown")
            
            # Network traffic widget cleanup
            if hasattr(self, 'network_traffic_widget') and self.network_traffic_widget:
                self.network_traffic_widget.cleanup()
                self.logger.info("Network traffic widget cleaned up during shutdown")
            
            # The PBOB widget handles its own unregistration from shared manager
            # No need to manage the shared Oph client directly
            
            self.logger.info("Housekeeping window cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during housekeeping window cleanup: {e}")
        
        event.accept() 

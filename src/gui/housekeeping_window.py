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
from src.config.settings import GUI, PR59_SERVER, HEATER_SERVER, BCP_HOUSEKEEPING
from src.gui.pbob_widget import PBoBWidget
from src.gui.pr59_widget import PR59Widget
from src.gui.heater_widget import HeaterWidget
from src.gui.network_traffic_widget import NetworkTrafficWidget
from src.gui.system_monitor_widget import SystemMonitorWidget
from src.gui.housekeeping_widget import HousekeepingWidget


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
        """Setup the housekeeping window UI layout with 3x2 grid + corner data logging button"""
        self.setWindowTitle("BVEX Ground Station - Housekeeping")
        
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: white; }")
        self.setCentralWidget(central_widget)
        
        # Main container layout
        container_layout = QVBoxLayout(central_widget)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)
        
        # Create widgets first
        self.setup_all_widgets()
        
        # Add simple data logging button at top corner
        self.setup_simple_data_logging_button()
        top_bar = QHBoxLayout()
        top_bar.addWidget(self.data_logging_button)
        top_bar.addStretch()  # Push button to left corner
        container_layout.addLayout(top_bar)
        
        # Main 3x2 grid layout
        main_layout = QGridLayout()
        main_layout.setSpacing(15)
        
        # ROW 0: Network Traffic Widget + System Monitor Widget (compact)
        main_layout.addWidget(self.network_traffic_widget, 0, 0, 2, 2)
        main_layout.addWidget(self.system_monitor_widget, 0, 4, 2, 4)
        
        # ROW 1: Housekeeping Widget + PBoB Widget
        main_layout.addWidget(self.housekeeping_widget, 0, 2, 2, 2)
        main_layout.addWidget(self.pbob_widget, 2, 4, 2, 4)
        
        # ROW 2: Heater Widget + PR59 Widget
        main_layout.addWidget(self.heater_widget, 4, 4, 2, 4)
        main_layout.addWidget(self.pr59_widget, 2, 0, 4, 4)
        
        # Set equal column stretch for 2-column layout
        #main_layout.setColumnStretch(0, 1)
        #main_layout.setColumnStretch(1, 1)
        
        # Set row stretch - equal for all 3 rows
        #main_layout.setRowStretch(0, 1)
        #main_layout.setRowStretch(1, 1)
        #main_layout.setRowStretch(2, 1)
        
        container_layout.addLayout(main_layout)
        
        # Set window properties for 3x2 grid layout
        width, height = self.get_safe_window_size(0.85, 0.90)  # Balanced dimensions
        self.setMinimumSize(max(1200, int(width*0.7)), max(1000, int(height*0.8)))
        self.resize(int(width*0.85), int(height*0.90))
            
    def setup_all_widgets(self):
        """Create all widgets used in the housekeeping window"""
        # System Monitor Widget (made VERY compact to match network traffic footprint)
        self.system_monitor_widget = SystemMonitorWidget(parent=self)
        self.system_monitor_widget.setMaximumWidth(350)  # Much more compact
        self.system_monitor_widget.setMaximumHeight(150)  # Compact height like network traffic
        
        # PBoB Widget (made more compact)
        self.pbob_widget = PBoBWidget(parent=self, oph_client=None)
        self.pbob_widget.setMaximumWidth(450)  # Make more compact
        
        # PR59 Widget
        self.pr59_widget = PR59Widget(
            parent=self, 
            server_ip=PR59_SERVER['host'], 
            server_port=PR59_SERVER['port']
        )
        
        # Heater Widget
        self.heater_widget = HeaterWidget(
            parent=self,
            server_ip=HEATER_SERVER['host'],
            server_port=HEATER_SERVER['port']
        )
        
        # NEW Housekeeping Widget
        self.housekeeping_widget = HousekeepingWidget(
            parent=self,
            server_ip=BCP_HOUSEKEEPING['host'],
            server_port=BCP_HOUSEKEEPING['port']
        )
        
        # Network Traffic Widget
        self.network_traffic_widget = NetworkTrafficWidget(
            parent=self,
            pointing_window=self.pointing_window,
            telescope_data_window=self.telescope_data_window,
            housekeeping_window=self
        )
    
    def setup_simple_data_logging_button(self):
        """Setup simple data logging button for corner placement"""
        # Simple toggle button - no fancy panel
        self.data_logging_button = QPushButton("Start Logging")
        self.data_logging_button.setMinimumHeight(30)
        self.data_logging_button.setMinimumWidth(120)
        self.data_logging_button.setMaximumWidth(150)
        self.data_logging_button.clicked.connect(self.toggle_data_logging)
        self.data_logging_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
    
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
            from src.data.loggers.system_monitor_logger import SystemMonitorDataLogger
            from src.data.loggers.housekeeping_logger import HousekeepingDataLogger

            # Initialize orchestrator
            self.data_logging_orchestrator = DataLoggingOrchestrator()
            
            # Register loggers for available widgets
            if self.pointing_window:
                if hasattr(self.pointing_window, 'gps_widget'):
                    gps_logger = GPSDataLogger(
                        self.data_logging_orchestrator.session_manager,
                        self.pointing_window.gps_widget
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
                
                # Register backend status logger
                if hasattr(self.telescope_data_window, 'backend_widget'):
                    from src.data.loggers.backend_logger import BackendDataLogger
                    backend_logger = BackendDataLogger(
                        self.data_logging_orchestrator.session_manager,
                        self.telescope_data_window.backend_widget
                    )
                    self.data_logging_orchestrator.register_logger('backend_status', backend_logger)
            
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
            
            # Register System Monitor logger
            system_monitor_logger = SystemMonitorDataLogger(
                self.data_logging_orchestrator.session_manager,
                self.system_monitor_widget
            )
            self.data_logging_orchestrator.register_logger('system_monitor', system_monitor_logger)
            
            # Register Housekeeping logger
            housekeeping_logger = HousekeepingDataLogger(
                self.data_logging_orchestrator.session_manager,
                self.housekeeping_widget
            )
            self.data_logging_orchestrator.register_logger('bcp_housekeeping', housekeeping_logger)
            
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
        """Update menu and simple button for data logging state"""
        if is_active:
            # Update menu action
            self.toggle_logging_action.setText('&Stop Data Logging')
            self.toggle_logging_action.setChecked(True)
            
            # Update simple button
            if hasattr(self, 'data_logging_button'):
                self.data_logging_button.setText("Stop Logging")
                self.data_logging_button.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
        else:
            # Update menu action
            self.toggle_logging_action.setText('&Start Data Logging')
            self.toggle_logging_action.setChecked(False)
            
            # Update simple button
            if hasattr(self, 'data_logging_button'):
                self.data_logging_button.setText("Start Logging")
                self.data_logging_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
        
        # Update system monitor widget logging indicator
        if hasattr(self, 'system_monitor_widget') and self.system_monitor_widget:
            self.system_monitor_widget.set_data_logging_active(is_active)
    
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
            
            # System monitor widget cleanup
            if hasattr(self, 'system_monitor_widget') and self.system_monitor_widget:
                self.system_monitor_widget.cleanup()
                self.logger.info("System monitor widget cleaned up during shutdown")
            
            # Housekeeping widget cleanup
            if hasattr(self, 'housekeeping_widget') and self.housekeeping_widget:
                self.housekeeping_widget.cleanup()
                self.logger.info("Housekeeping widget cleaned up during shutdown")
            
            # The PBOB widget handles its own unregistration from shared manager
            # No need to manage the shared Oph client directly
            
            self.logger.info("Housekeeping window cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during housekeeping window cleanup: {e}")
        
        event.accept() 

#!/usr/bin/env python3
"""
BVEX Ground Station - Main Entry Point
Balloon-borne VLBI Experiment Ground Station Software

Usage: python main.py
"""

import sys
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.gui.pointing_window import PointingWindow
from src.gui.telescope_data_window import TelescopeDataWindow  
from src.gui.housekeeping_window import HousekeepingWindow
from src.data.gps_client import GPSClient
from src.data.Oph_client import OphClient


def setup_logging():
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(log_dir, f'bvex_ground_station_{timestamp}.log')
    
    # Create rotating file handler (max 10MB per file, keep 5 files)
    file_handler = RotatingFileHandler(
        log_filename, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler for errors only (not warnings)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce verbosity of third-party libraries
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"BVEX Ground Station logging started - Log file: {log_filename}")
    print(f"BVEX Ground Station started - Logs written to: {log_filename}")
    print("Console will only show warnings and errors. All detailed logs are in the file.")
    
    return logger


def cleanup_old_logs(log_dir):
    """Clean up log files older than 30 days"""
    try:
        import time
        
        current_time = time.time()
        thirty_days_ago = current_time - (30 * 24 * 60 * 60)  # 30 days in seconds
        
        for filename in os.listdir(log_dir):
            if filename.startswith('bvex_ground_station_') and filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < thirty_days_ago:
                        os.remove(file_path)
                        print(f"Cleaned up old log file: {filename}")
    except Exception as e:
        print(f"Warning: Failed to clean up old logs: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("BVEX Ground Station Multi-Window")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("BVEX Team")
    
    # Setup logging
    logger = setup_logging()
    cleanup_old_logs('logs')
    
    try:
        # Create shared clients
        logger.info("Creating shared clients...")
        gps_client = GPSClient()
        shared_oph_client = OphClient()
        
        # Start shared OphClient 
        if shared_oph_client.start():
            logger.info("Shared OphClient started successfully")
        else:
            logger.error("Failed to start shared OphClient")
        
        # Create the three windows
        logger.info("Creating application windows...")
        
        pointing_window = PointingWindow(gps_client=gps_client, shared_oph_client=shared_oph_client)
        telescope_data_window = TelescopeDataWindow()
        housekeeping_window = HousekeepingWindow(
            pointing_window=pointing_window, 
            telescope_data_window=telescope_data_window,
            shared_oph_client=shared_oph_client
        )
        
        # Position windows to avoid overlap
        pointing_window.move(100, 100)
        telescope_data_window.move(800, 100)  
        housekeeping_window.move(1500, 100)
        
        # Show all windows
        pointing_window.show()
        telescope_data_window.show()
        housekeeping_window.show()
        
        logger.info("All windows created and displayed successfully")
        print("BVEX Ground Station Multi-Window Interface Ready!")
        print("Three windows opened:")
        print("1. Pointing Window - Sky chart, star camera, GPS, motor control")
        print("2. Telescope Data Window - Spectrometer and scientific data")
        print("3. Housekeeping Window - Data logging and system monitoring")
        
        # Start event loop
        result = app.exec()
        
        # Cleanup on exit
        logger.info("Application shutting down...")
        if shared_oph_client:
            shared_oph_client.cleanup()
        if gps_client:
            gps_client.cleanup()
            
        logger.info("BVEX Ground Station shutdown complete")
        sys.exit(result)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
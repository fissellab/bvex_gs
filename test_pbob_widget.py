#!/usr/bin/env python3
"""
Test script for PBOB Widget functionality
Tests PBOB widget connection and data display
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from src.gui.pbob_widget import PBoBWidget
from src.data.Oph_client import OphClient
import time

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PBOB Widget Test")
        self.setGeometry(100, 100, 800, 500)
        
        # Create Oph client
        self.oph_client = OphClient()
        
        # Create central widget
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Create PBOB widget
        self.pbob_widget = PBoBWidget(parent=self, oph_client=self.oph_client)
        layout.addWidget(self.pbob_widget)
        
        self.setCentralWidget(central_widget)
        
        # Start Oph client
        print("Starting Oph client...")
        if self.oph_client.start():
            print("✅ Oph client started successfully")
            # Resume it to get data
            self.oph_client.resume()
            print("✅ Oph client resumed for data collection")
        else:
            print("❌ Failed to start Oph client")

def main():
    app = QApplication(sys.argv)
    
    print("PBOB Widget Test")
    print("================")
    print("This test will create a PBOB widget and test its connection to the Oph server.")
    print("You should see subsystem power states and current measurements.")
    print("")
    
    window = TestWindow()
    window.show()
    
    print("Test window opened. Check if PBOB widget shows 'Connected' status")
    print("and displays current measurements for subsystems.")
    print("Close the window to exit the test.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
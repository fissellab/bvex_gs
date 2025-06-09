#!/usr/bin/env python3
"""
Test script for GPS Map Widget
Simple test of the offline Ontario map functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer
from src.gui.gps_map_widget import GPSMapWidget
from src.data.gps_client import GPSClient, GPSData
import time

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Map Widget Test - Ontario Offline Map")
        self.setGeometry(100, 100, 400, 500)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Info label
        info = QLabel("Testing Offline Ontario Map with Real GPS Data")
        info.setStyleSheet("QLabel { font-weight: bold; padding: 10px; }")
        layout.addWidget(info)
        
        # Create map widget
        self.map_widget = GPSMapWidget()
        layout.addWidget(self.map_widget)
        
        # Test with current GPS coordinates (stationary balloon)
        test_button = QPushButton("Update with Current GPS Position")
        test_button.clicked.connect(self.test_current_position)
        layout.addWidget(test_button)
        
        # Status label
        self.status_label = QLabel("Click button to test with GPS coordinates")
        self.status_label.setStyleSheet("QLabel { padding: 5px; color: #666; }")
        layout.addWidget(self.status_label)
    
    def test_current_position(self):
        """Test with a realistic GPS position near Kingston"""
        # Use coordinates similar to what we're getting from the GPS server
        test_lat = 44.22446  # Near Kingston area
        test_lon = -76.49732
        
        print(f"Testing map with position: {test_lat:.5f}, {test_lon:.5f}")
        self.map_widget.update_position(test_lat, test_lon)
        
        self.status_label.setText(f"Map updated with position: {test_lat:.5f}, {test_lon:.5f}")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("GPS Map Widget Test Started - Offline Ontario Map")
    print("- Shows Ontario map with ground station and balloon positions")
    print("- No internet connection required")
    print("- Click button to test with GPS coordinates")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
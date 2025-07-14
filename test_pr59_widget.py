#!/usr/bin/env python3
"""
Test script for PR59 Widget functionality
Tests the PR59 client and widget independently
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from src.gui.pr59_widget import PR59Widget
from src.data.pr59_client import PR59Client
from src.config.settings import PR59_SERVER
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_pr59_client():
    """Test PR59 client functionality"""
    print("Testing PR59 Client...")
    print(f"Server: {PR59_SERVER['host']}:{PR59_SERVER['port']}")
    client = PR59Client(server_ip=PR59_SERVER['host'], server_port=PR59_SERVER['port'])
    
    # Test individual channel requests
    print("\nTesting individual channels:")
    for channel in ["pr59_temp", "pr59_voltage", "pr59_current", "pr59_running", "pr59_status"]:
        value = client.get_telemetry(channel)
        print(f"  {channel}: {value}")
    
    # Test data update
    print("\nTesting data update...")
    success = client.update_data()
    data = client.get_data()
    
    print(f"Update successful: {success}")
    print(f"Data valid: {data.valid}")
    print(f"Server responding: {client.is_server_responding()}")
    if data.valid:
        print(f"Temperature: {data.temp:.2f}°C")
        print(f"Current: {data.current:.3f}A")
        print(f"Voltage: {data.voltage:.3f}V")
        print(f"Power: {data.power:.3f}W")
        print(f"Running: {data.running}")
        print(f"Status: {data.status}")
    
    print(f"Connection status: {client.get_connection_status()}")
    return success or client.is_server_responding()

def test_pr59_widget():
    """Test PR59 widget in a simple window"""
    print("\nTesting PR59 Widget...")
    
    app = QApplication(sys.argv)
    
    # Create a simple test window
    window = QMainWindow()
    window.setWindowTitle("PR59 Widget Test")
    
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Create PR59 widget with Sagittarius server IP
    pr59_widget = PR59Widget(
        parent=window, 
        server_ip=PR59_SERVER['host'], 
        server_port=PR59_SERVER['port']
    )
    layout.addWidget(pr59_widget)
    
    window.setCentralWidget(central_widget)
    window.resize(800, 500)
    window.show()
    
    print("PR59 Widget created successfully!")
    print("Close the window to continue...")
    
    # Run for a short time to test functionality
    return app.exec()

def main():
    """Main test function"""
    print("PR59 Widget Test Suite")
    print("=" * 50)
    
    # Test client first
    client_success = test_pr59_client()
    
    if client_success:
        print("\nClient test passed! Testing widget...")
        test_pr59_widget()
    else:
        print("\nClient test failed. This is expected if the PR59 server is not running.")
        print("Widget test will still work, but will show 'Disconnected' status.")
        
        # Ask user if they want to test widget anyway
        response = input("\nTest widget anyway? (y/n): ")
        if response.lower() == 'y':
            test_pr59_widget()

if __name__ == "__main__":
    main() 
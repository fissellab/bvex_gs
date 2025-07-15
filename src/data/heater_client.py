"""
Heater System UDP Client for BVEX Ground Station
Sends relay toggle commands to the heater system and tracks status
"""

import socket
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from src.config.settings import HEATER_SERVER


@dataclass
class HeaterData:
    """Data container for heater system status"""
    
    def __init__(self):
        self.valid = False
        self.timestamp = 0.0
        
        # Relay states (True = ON, False = OFF, None = Unknown)
        self.lockpin_state = None      # Relay 0 - Lock pin heater (temp-controlled)
        self.starcamera_state = None   # Relay 1 - Star camera heater (temp-controlled) 
        self.pv_state = None          # Relay 2 - PV panel heater (temp-controlled)
        self.motor_state = None       # Relay 3 - Motor heater (temp-controlled)
        self.ethernet_state = None    # Relay 4 - Ethernet switch heater (manual-only)
        
        # Temperature readings (would need to be added to server if available)
        self.lockpin_temp = 0.0
        self.starcamera_temp = 0.0
        self.pv_temp = 0.0
        self.motor_temp = 0.0
        
        # Current measurements (3A total limit)
        self.total_current = 0.0
        
        # System status
        self.system_online = False
        self.last_command_success = None
        self.last_error = ""


class HeaterClient:
    """UDP client for heater system control"""
    
    def __init__(self, host=None, port=None, timeout=None):
        self.logger = logging.getLogger(__name__)
        self.host = host or HEATER_SERVER['host']
        self.port = port or HEATER_SERVER['port'] 
        self.timeout = timeout or HEATER_SERVER['timeout']
        
        # Current data
        self.current_data = HeaterData()
        self.last_update_time = 0.0
        
        # Connection tracking
        self.connection_attempts = 0
        self.last_connection_attempt = 0.0
        self.consecutive_failures = 0
        
        # Available commands mapping
        self.heater_commands = {
            'lockpin': 'toggle_lockpin',
            'starcamera': 'toggle_starcamera', 
            'pv': 'toggle_PV',
            'motor': 'toggle_motor',
            'ethernet': 'toggle_ethernet'
        }
        
        self.logger.info(f"Heater client initialized - Server: {self.host}:{self.port}")
    
    def send_command(self, command: str) -> bool:
        """Send command and return success status"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            self.connection_attempts += 1
            self.last_connection_attempt = time.time()
            
            # Send command
            sock.sendto(command.encode(), (self.host, self.port))
            
            # Receive response
            response, _ = sock.recvfrom(1024)
            response_str = response.decode().strip()
            
            # Check success (server returns "1" for success, "0" for failure)
            success = response_str == "1"
            
            if success:
                self.consecutive_failures = 0
                self.current_data.last_command_success = True
                self.current_data.system_online = True
                self.logger.debug(f"Command '{command}' executed successfully")
            else:
                self.consecutive_failures += 1
                self.current_data.last_command_success = False
                self.current_data.last_error = f"Server returned: {response_str}"
                self.logger.warning(f"Command '{command}' failed - Server response: {response_str}")
            
            sock.close()
            return success
            
        except socket.timeout:
            self.consecutive_failures += 1
            self.current_data.last_command_success = False
            self.current_data.system_online = False
            self.current_data.last_error = f"Timeout after {self.timeout}s"
            self.logger.warning(f"Command '{command}' timed out")
            return False
            
        except Exception as e:
            self.consecutive_failures += 1
            self.current_data.last_command_success = False
            self.current_data.system_online = False
            self.current_data.last_error = str(e)
            self.logger.error(f"Command '{command}' failed: {e}")
            return False
    
    def toggle_lockpin(self) -> bool:
        """Toggle lock pin heater (relay 0)"""
        return self.send_command("toggle_lockpin")
    
    def toggle_starcamera(self) -> bool:
        """Toggle star camera heater (relay 1)"""
        return self.send_command("toggle_starcamera")
    
    def toggle_pv(self) -> bool:
        """Toggle PV panel heater (relay 2)"""
        return self.send_command("toggle_PV")
    
    def toggle_motor(self) -> bool:
        """Toggle motor heater (relay 3)"""
        return self.send_command("toggle_motor")
    
    def toggle_ethernet(self) -> bool:
        """Toggle ethernet switch heater (relay 4)"""
        return self.send_command("toggle_ethernet")
    
    def get_current_data(self) -> HeaterData:
        """Get current heater data"""
        current_time = time.time()
        self.current_data.timestamp = current_time
        
        # Update validity based on recent activity
        time_since_last_attempt = current_time - self.last_connection_attempt
        self.current_data.valid = time_since_last_attempt < 30.0  # Valid if attempted in last 30s
        
        return self.current_data
    
    def test_connection(self) -> bool:
        """Test connection to heater server by sending a command"""
        # Use lockpin toggle as a test (could toggle back if needed)
        return self.send_command("toggle_lockpin")
    
    def is_connected(self) -> bool:
        """Check if server is responding based on recent attempts"""
        if self.consecutive_failures > 3:
            return False
        
        current_time = time.time()
        time_since_last_attempt = current_time - self.last_connection_attempt
        
        # Consider connected if we've had recent successful communication
        return (time_since_last_attempt < 60.0 and 
                self.current_data.last_command_success is not False)
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Heater client cleaned up") 
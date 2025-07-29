"""
Heater System UDP Client for BVEX Ground Station
Implements heater control commands and telemetry according to HEATER_CLIENT_GUIDE.md
"""

import socket
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from src.config.settings import HEATER_SERVER, HEATER_TELEMETRY


@dataclass
class HeaterData:
    """Data container for heater system status"""
    
    def __init__(self):
        self.valid = False
        self.timestamp = 0.0
        
        # Individual heater states (True = ON, False = OFF, None = Unknown)
        # According to guide - mapping commands to actual components
        self.starcam_state = None      # Heater ID 0 - toggle_lockpin controls star camera
        self.motor_state = None        # Heater ID 1 - toggle_starcamera controls motor  
        self.ethernet_state = None     # Heater ID 2 - toggle_PV controls ethernet
        self.lockpin_state = None      # Heater ID 3 - toggle_motor controls lock pin
        self.spare_state = None        # Heater ID 4 - toggle_ethernet controls spare (manual only)
        
        # Temperature readings (°C)
        self.starcam_temp = 0.0
        self.motor_temp = 0.0
        self.ethernet_temp = 0.0
        self.lockpin_temp = 0.0
        self.spare_temp = 0.0
        
        # Current consumption (A)
        self.starcam_current = 0.0
        self.motor_current = 0.0
        self.ethernet_current = 0.0
        self.lockpin_current = 0.0
        self.spare_current = 0.0
        
        # System status
        self.total_current = 0.0
        self.system_running = False
        self.system_online = False
        self.last_command_success = None
        self.last_error = ""


class HeaterTelemetryClient:
    """Telemetry client for reading heater status and sensor data"""
    
    def __init__(self, host=None, port=None, timeout=None):
        self.host = host or HEATER_TELEMETRY['host']
        self.port = port or HEATER_TELEMETRY['port']
        self.timeout = timeout or HEATER_TELEMETRY['timeout']
        self.logger = logging.getLogger(__name__)
        
    def get_telemetry(self, channel: str) -> str:
        """Get telemetry value for specified channel"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Send telemetry request
            sock.sendto(channel.encode(), (self.host, self.port))
            response, _ = sock.recvfrom(1024)
            
            sock.close()
            return response.decode().strip()
            
        except socket.timeout:
            self.logger.warning(f"Telemetry timeout for channel: {channel}")
            return "TIMEOUT"
        except Exception as e:
            self.logger.error(f"Telemetry error for channel {channel}: {e}")
            return f"ERROR: {e}"
    
    def get_heater_status(self) -> Dict[str, Any]:
        """Get comprehensive heater status according to guide"""
        status = {}
        
        # System status
        status['running'] = self.get_telemetry('heater_running')
        status['total_current'] = self.get_telemetry('heater_total_current')
        
        # Individual heater data - using guide naming convention
        heaters = ['starcam', 'motor', 'ethernet', 'lockpin', 'spare']
        for heater in heaters:
            status[heater] = {
                'temp': self.get_telemetry(f'heater_{heater}_temp'),
                'current': self.get_telemetry(f'heater_{heater}_current'),
                'state': self.get_telemetry(f'heater_{heater}_state')
            }
        
        return status


class HeaterClient:
    """UDP client for heater system control according to HEATER_CLIENT_GUIDE.md"""
    
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
        
        # Telemetry client for reading system status
        self.telemetry_client = HeaterTelemetryClient()
        
        self.logger.info(f"Heater client initialized - Command server: {self.host}:{self.port}")
        self.logger.info(f"Telemetry server: {self.telemetry_client.host}:{self.telemetry_client.port}")
    
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
    
    # Command methods according to HEATER_CLIENT_GUIDE.md
    # Note: Command names vs components are as specified in the guide
    
    def toggle_starcam_auto(self) -> bool:
        """Toggle automatic control for star camera heater (command: toggle_lockpin)"""
        return self.send_command("toggle_lockpin")
    
    def toggle_motor_auto(self) -> bool:
        """Toggle automatic control for motor heater (command: toggle_starcamera)"""
        return self.send_command("toggle_starcamera")
    
    def toggle_ethernet_auto(self) -> bool:
        """Toggle automatic control for ethernet heater (command: toggle_PV)"""
        return self.send_command("toggle_PV")
    
    def toggle_lockpin_auto(self) -> bool:
        """Toggle automatic control for lock pin heater (command: toggle_motor)"""
        return self.send_command("toggle_motor")
    
    def toggle_spare_heater(self) -> bool:
        """Toggle spare heater ON/OFF directly (command: toggle_ethernet)"""
        return self.send_command("toggle_ethernet")
    
    # Legacy method names for backwards compatibility
    def toggle_lockpin(self) -> bool:
        """Legacy: Toggle star camera heater (use toggle_starcam_auto instead)"""
        self.logger.warning("Using legacy method toggle_lockpin - this controls STAR CAMERA, not lock pin!")
        return self.toggle_starcam_auto()
    
    def toggle_starcamera(self) -> bool:
        """Legacy: Toggle motor heater (use toggle_motor_auto instead)"""
        self.logger.warning("Using legacy method toggle_starcamera - this controls MOTOR, not star camera!")
        return self.toggle_motor_auto()
    
    def toggle_pv(self) -> bool:
        """Legacy: Toggle ethernet heater (use toggle_ethernet_auto instead)"""
        self.logger.warning("Using legacy method toggle_pv - this controls ETHERNET, not PV!")
        return self.toggle_ethernet_auto()
    
    def toggle_motor(self) -> bool:
        """Legacy: Toggle lock pin heater (use toggle_lockpin_auto instead)"""
        self.logger.warning("Using legacy method toggle_motor - this controls LOCK PIN, not motor!")
        return self.toggle_lockpin_auto()
    
    def toggle_ethernet(self) -> bool:
        """Legacy: Toggle spare heater (use toggle_spare_heater instead)"""
        self.logger.warning("Using legacy method toggle_ethernet - this controls SPARE heater, not ethernet!")
        return self.toggle_spare_heater()
    
    def update_telemetry_data(self) -> bool:
        """Update heater data from telemetry system"""
        try:
            # Get comprehensive status from telemetry
            status = self.telemetry_client.get_heater_status()
            
            # Update system status
            self.current_data.system_running = status.get('running', '0') == '1'
            
            try:
                self.current_data.total_current = float(status.get('total_current', '0'))
            except (ValueError, TypeError):
                self.current_data.total_current = 0.0
            
            # Update individual heater data
            heaters_map = {
                'starcam': 'starcam',
                'motor': 'motor', 
                'ethernet': 'ethernet',
                'lockpin': 'lockpin',
                'spare': 'spare'
            }
            
            for heater_key, data_attr in heaters_map.items():
                heater_data = status.get(heater_key, {})
                
                # Temperature
                try:
                    temp_val = float(heater_data.get('temp', '0'))
                    setattr(self.current_data, f'{data_attr}_temp', temp_val)
                except (ValueError, TypeError):
                    setattr(self.current_data, f'{data_attr}_temp', 0.0)
                
                # Current
                try:
                    current_val = float(heater_data.get('current', '0'))
                    setattr(self.current_data, f'{data_attr}_current', current_val)
                except (ValueError, TypeError):
                    setattr(self.current_data, f'{data_attr}_current', 0.0)
                
                # State
                state_str = heater_data.get('state', '-1')
                if state_str == '1':
                    setattr(self.current_data, f'{data_attr}_state', True)
                elif state_str == '0':
                    setattr(self.current_data, f'{data_attr}_state', False)
                else:
                    setattr(self.current_data, f'{data_attr}_state', None)
            
            self.current_data.valid = True
            self.current_data.timestamp = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating telemetry data: {e}")
            self.current_data.valid = False
            return False
    
    def get_current_data(self) -> HeaterData:
        """Get current heater data"""
        current_time = time.time()
        
        # Update telemetry data
        self.update_telemetry_data()
        
        # Update validity based on recent activity
        time_since_last_attempt = current_time - self.last_connection_attempt
        self.current_data.valid = self.current_data.valid and (time_since_last_attempt < 30.0)
        
        return self.current_data
    
    def test_connection(self) -> bool:
        """Test connection to heater server"""
        return self.send_command("toggle_lockpin")  # Test command
    
    def is_connected(self) -> bool:
        """Check if server is responding based on recent attempts"""
        if self.consecutive_failures > 3:
            return False
        
        current_time = time.time()
        time_since_last_attempt = current_time - self.last_connection_attempt
        
        # Consider connected if we've had recent successful communication
        return (time_since_last_attempt < 60.0 and 
                self.current_data.last_command_success is not False)
    
    def close(self):
        """Close connections (compatibility with guide examples)"""
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Heater client cleaned up") 
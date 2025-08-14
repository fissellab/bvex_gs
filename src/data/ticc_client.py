"""
TICC (Time Interval Counter) Client for BVEX Ground Station
Measures PPS timing differences between GPS and OCXO signals via UDP telemetry
"""

import socket
import time
import logging
from dataclasses import dataclass
from typing import Optional

from src.config.settings import VLBI_SERVER  # Using same server as VLBI


@dataclass
class TICCData:
    """Data structure for TICC measurements"""
    
    def __init__(self):
        # TICC measurement fields
        self.timestamp: float = 0.0            # Unix timestamp of last measurement
        self.interval: float = 0.0             # Time interval difference in seconds
        self.logging: bool = False             # Is TICC actively logging?
        self.measurement_count: int = 0        # Total measurements taken
        self.current_file: str = ""            # Current data file path
        self.configured: bool = False          # Is TICC configured?
        
        # Status tracking
        self.last_fetch_time = 0.0
        self.valid: bool = False               # Indicates if data is valid


class TICCClient:
    """UDP client for TICC telemetry from Saggitarius server"""
    
    def __init__(self, server_ip=None, server_port=None, timeout=None):
        # Use same server as VLBI (Saggitarius system with telemetry on port 8082)
        self.server_ip = server_ip or VLBI_SERVER['host']  # '100.70.234.8'
        self.server_port = server_port or VLBI_SERVER['port']  # 8082
        self.timeout = timeout or VLBI_SERVER['timeout']  # 5.0
        self.logger = logging.getLogger(__name__)
        
        # Current data
        self.current_data = TICCData()
        self.last_update_time = 0.0
        
        # Connection tracking
        self.connection_attempts = 0
        self.last_connection_attempt = 0.0
        self.consecutive_failures = 0
        
        # Data rate tracking
        self.bytes_received = 0
        self.last_rate_check = time.time()
        
        self.logger.info(f"TICC client initialized - Server: {self.server_ip}:{self.server_port}")
    
    def get_telemetry(self, channel_name: str) -> str:
        """Request specific telemetry data from TICC server"""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Send request
            request = channel_name.encode('utf-8')
            sock.sendto(request, (self.server_ip, self.server_port))
            
            # Receive response
            response, addr = sock.recvfrom(1024)
            sock.close()
            
            # Track data rate
            self.bytes_received += len(response)
            
            return response.decode('utf-8').strip()
        
        except socket.timeout:
            self.consecutive_failures += 1
            return "TIMEOUT"
        except Exception as e:
            self.logger.debug(f"Error getting {channel_name}: {e}")
            self.consecutive_failures += 1
            return f"ERROR: {e}"
    
    def get_comprehensive_status(self) -> str:
        """Get all TICC data using GET_TICC command"""
        return self.get_telemetry("GET_TICC")
    
    def update_data(self) -> bool:
        """Update all TICC telemetry data using comprehensive command"""
        try:
            # Get comprehensive TICC data in one request
            response = self.get_comprehensive_status()
            
            if response in ["TIMEOUT", "N/A"] or response.startswith("ERROR"):
                self.current_data.valid = False
                self.consecutive_failures += 1
                return False
            
            # Parse response: "ticc_timestamp:1754494408.000,ticc_interval:-0.47321053853,ticc_logging:1,ticc_measurement_count:1234"
            try:
                data_dict = {}
                for item in response.split(','):
                    if ':' in item:
                        key, value = item.split(':', 1)
                        data_dict[key.strip()] = value.strip()
                
                # Update current data
                self.current_data.timestamp = float(data_dict.get('ticc_timestamp', 0.0))
                self.current_data.interval = float(data_dict.get('ticc_interval', 0.0))
                self.current_data.logging = bool(int(data_dict.get('ticc_logging', 0)))
                self.current_data.measurement_count = int(data_dict.get('ticc_measurement_count', 0))
                
                # Get additional status if needed
                status_response = self.get_telemetry("ticc_status")
                if status_response not in ["TIMEOUT", "N/A"] and not status_response.startswith("ERROR"):
                    # Parse status: "logging:yes,configured:yes,measurements:1234"
                    status_dict = {}
                    for item in status_response.split(','):
                        if ':' in item:
                            key, value = item.split(':', 1)
                            status_dict[key.strip()] = value.strip()
                    
                    self.current_data.configured = status_dict.get('configured', 'no').lower() == 'yes'
                
                # Get current file
                file_response = self.get_telemetry("ticc_current_file")
                if file_response not in ["TIMEOUT", "N/A"] and not file_response.startswith("ERROR"):
                    self.current_data.current_file = file_response
                
                self.current_data.valid = True
                self.current_data.last_fetch_time = time.time()
                self.last_update_time = time.time()
                self.consecutive_failures = 0
                
                return True
                
            except (ValueError, KeyError) as e:
                self.logger.error(f"Failed to parse TICC response '{response}': {e}")
                self.current_data.valid = False
                return False
        
        except Exception as e:
            self.logger.error(f"Error updating TICC data: {e}")
            self.current_data.valid = False
            return False
    
    def is_connected(self) -> bool:
        """Check if TICC client is connected to server"""
        return (self.consecutive_failures < 3 and 
                time.time() - self.last_update_time < 30.0)  # Consider connected if updated within 30s
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate in KB/s"""
        current_time = time.time()
        time_diff = current_time - self.last_rate_check
        
        if time_diff > 0:
            rate_bps = self.bytes_received / time_diff
            self.bytes_received = 0  # Reset counter
            self.last_rate_check = current_time
            return rate_bps / 1024.0  # Convert to KB/s
        
        return 0.0
    
    def get_interval_seconds(self) -> float:
        """Get current time interval measurement in seconds"""
        if self.current_data.valid:
            return self.current_data.interval
        return 0.0
    
    def get_measurement_count(self) -> int:
        """Get total measurement count"""
        if self.current_data.valid:
            return self.current_data.measurement_count
        return 0
    
    def is_logging(self) -> bool:
        """Check if TICC is actively logging"""
        if self.current_data.valid:
            return self.current_data.logging
        return False
    
    def cleanup(self):
        """Clean up TICC client resources"""
        self.logger.info("TICC client cleaned up")
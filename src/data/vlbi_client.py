"""
VLBI Telemetry Client for BVEX Ground Station
Connects to Saggitarius telemetry server for real-time VLBI status data
"""

import socket
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from src.config.settings import VLBI_SERVER


@dataclass
class VLBIData:
    """Data structure for VLBI telemetry"""
    def __init__(self):
        # VLBI status fields
        self.running = 0
        self.stage = "stopped"
        self.packets = 0
        self.data_mb = 0.0
        self.connection = "disconnected"
        self.errors = 0
        self.pid = 0
        self.last_update = ""
        
        # Status tracking
        self.valid = False
        self.last_fetch_time = 0.0


class VLBITelemetryClient:
    """UDP client for VLBI telemetry from Saggitarius server"""
    
    def __init__(self, server_ip=None, server_port=None, timeout=None):
        self.server_ip = server_ip or VLBI_SERVER['host']
        self.server_port = server_port or VLBI_SERVER['port']
        self.timeout = timeout or VLBI_SERVER['timeout']
        self.logger = logging.getLogger(__name__)
        
        # Current data
        self.current_data = VLBIData()
        self.last_update_time = 0.0
        
        # Connection tracking
        self.connection_attempts = 0
        self.last_connection_attempt = 0.0
        self.consecutive_failures = 0
        
        # Data rate tracking
        self.bytes_received = 0
        self.last_rate_check = time.time()
        
        self.logger.info(f"VLBI telemetry client initialized - Server: {server_ip}:{server_port}")
    
    def get_telemetry(self, channel_name: str) -> str:
        """Request specific telemetry data from VLBI server"""
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
        """Get all VLBI data using GET_VLBI command"""
        return self.get_telemetry("GET_VLBI")
    
    def parse_comprehensive_status(self, status_string: str) -> Dict[str, str]:
        """Parse GET_VLBI response into dictionary"""
        try:
            if status_string in ["TIMEOUT", "N/A"] or status_string.startswith("ERROR"):
                return {}
                
            # Parse CSV format: vlbi_running:1,vlbi_stage:capturing,vlbi_packets:15420,...
            fields = {}
            for item in status_string.split(','):
                if ':' in item:
                    key, value = item.split(':', 1)
                    fields[key.strip()] = value.strip()
            return fields
            
        except Exception as e:
            self.logger.error(f"Error parsing VLBI status: {e}")
            return {}
    
    def update_data(self) -> bool:
        """Update all VLBI telemetry data"""
        try:
            current_time = time.time()
            self.last_update_time = current_time
            self.connection_attempts += 1
            
            # Get comprehensive status
            status_response = self.get_comprehensive_status()
            
            # Handle different error responses
            if status_response == "TIMEOUT":
                self.logger.warning("VLBI server connection timeout")
                self.current_data.valid = False
                return False
            elif status_response == "ERROR:UNKNOWN_REQUEST":
                self.logger.warning("VLBI commands not available on telemetry server - VLBI may not be running")
                # Set mock data to show the widget works but VLBI isn't available
                self._set_mock_unavailable_data()
                self.current_data.valid = True  # Valid response, just no VLBI
                return True
            elif status_response.startswith("ERROR"):
                self.logger.error(f"VLBI server error: {status_response}")
                self.current_data.valid = False
                return False
            elif status_response == "N/A":
                self.logger.info("VLBI not available")
                self._set_mock_unavailable_data()
                self.current_data.valid = True
                return True
            
            # Parse the response
            fields = self.parse_comprehensive_status(status_response)
            
            if fields:
                # Update data structure with real data
                self.current_data.running = int(fields.get('vlbi_running', '0'))
                self.current_data.stage = fields.get('vlbi_stage', 'unknown')
                self.current_data.packets = int(fields.get('vlbi_packets', '0'))
                self.current_data.data_mb = float(fields.get('vlbi_data_mb', '0.0'))
                self.current_data.connection = fields.get('vlbi_connection', 'unknown')
                self.current_data.errors = int(fields.get('vlbi_errors', '0'))
                self.current_data.pid = int(fields.get('vlbi_pid', '0'))
                self.current_data.last_update = fields.get('vlbi_last_update', '')
                
                self.current_data.valid = True
                self.current_data.last_fetch_time = current_time
                self.consecutive_failures = 0
                return True
            else:
                self.current_data.valid = False
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating VLBI data: {e}")
            self.current_data.valid = False
            return False
    
    def _set_mock_unavailable_data(self):
        """Set mock data when VLBI is not available but connection works"""
        current_time = time.time()
        self.current_data.running = 0
        self.current_data.stage = "not_available"
        self.current_data.packets = 0
        self.current_data.data_mb = 0.0
        self.current_data.connection = "not_available"
        self.current_data.errors = 0
        self.current_data.pid = 0
        self.current_data.last_update = ""
        self.current_data.last_fetch_time = current_time
        self.consecutive_failures = 0
    
    def get_data_rate_kbps(self) -> float:
        """Calculate current data rate in KB/s"""
        current_time = time.time()
        time_elapsed = current_time - self.last_rate_check
        
        if time_elapsed >= 1.0:  # Update rate every second
            rate_kbps = (self.bytes_received / 1024.0) / time_elapsed
            
            # Reset counters
            self.bytes_received = 0
            self.last_rate_check = current_time
            
            return rate_kbps
        
        return 0.0
    
    def is_connected(self) -> bool:
        """Check if we have recent valid data"""
        if not self.current_data.valid:
            return False
            
        # Consider connected if we have data from last 30 seconds
        time_since_update = time.time() - self.current_data.last_fetch_time
        return time_since_update < 30.0
    
    def should_attempt_connection(self) -> bool:
        """Determine if we should attempt a connection based on failure history"""
        if self.consecutive_failures == 0:
            return True
            
        # Exponential backoff with max delay of 60 seconds
        backoff_time = min(2 ** min(self.consecutive_failures, 6), 60)
        time_since_last_attempt = time.time() - self.last_connection_attempt
        
        return time_since_last_attempt >= backoff_time
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("VLBI telemetry client cleaned up")
"""
Aquila Backend Client for BVEX Ground Station
Connects to Saggitarius telemetry server to get Aquila backend status
"""

import socket
import time
import logging
from dataclasses import dataclass
from typing import Optional
from src.config.settings import VLBI_SERVER


@dataclass
class AquilaData:
    """Data structure for Aquila backend system status"""
    
    def __init__(self):
        # SSD1 status
        self.ssd1_mounted: bool = False
        self.ssd1_percent: float = 0.0
        self.ssd1_used_gb: float = 0.0
        self.ssd1_total_gb: float = 0.0
        
        # SSD2 status  
        self.ssd2_mounted: bool = False
        self.ssd2_percent: float = 0.0
        self.ssd2_used_gb: float = 0.0
        self.ssd2_total_gb: float = 0.0
        
        # System status
        self.cpu_temp: float = 0.0
        self.memory_percent: float = 0.0
        
        # Metadata
        self.last_update_time: float = 0.0
        self.valid: bool = False


class AquilaClient:
    """UDP client for Aquila backend telemetry from Saggitarius server"""
    
    def __init__(self, server_ip=None, server_port=None, timeout=None):
        # Use same server as VLBI (Saggitarius system with telemetry on port 8082)
        self.server_ip = server_ip or VLBI_SERVER['host']  # '172.20.4.170'
        self.server_port = server_port or VLBI_SERVER['port']  # 8082
        self.timeout = timeout or VLBI_SERVER['timeout']  # 5.0
        self.logger = logging.getLogger(__name__)
        
        # Current data
        self.current_data = AquilaData()
        self.last_update_time = 0.0
        
        # Connection tracking
        self.connection_attempts = 0
        self.last_connection_attempt = 0.0
        self.consecutive_failures = 0
        
        # Data rate tracking
        self.bytes_received = 0
        self.last_rate_check = time.time()
        
        self.logger.info(f"Aquila client initialized - Server: {self.server_ip}:{self.server_port}")
    
    def get_telemetry(self, channel_name: str) -> str:
        """Request specific telemetry data from Aquila backend via Saggitarius server"""
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
        """Get all Aquila data using GET_AQUILA command"""
        return self.get_telemetry("GET_AQUILA")
    
    def update_data(self) -> bool:
        """Update all Aquila backend data from telemetry server"""
        try:
            self.connection_attempts += 1
            self.last_connection_attempt = time.time()
            
            # Get individual metrics (as per TELEMETRY_INTEGRATION_COMPLETE.md)
            ssd1_mounted = self.get_telemetry("aquila_ssd1_mounted")
            ssd1_percent = self.get_telemetry("aquila_ssd1_percent")
            ssd1_used_gb = self.get_telemetry("aquila_ssd1_used_gb")
            ssd1_total_gb = self.get_telemetry("aquila_ssd1_total_gb")
            
            ssd2_mounted = self.get_telemetry("aquila_ssd2_mounted")
            ssd2_percent = self.get_telemetry("aquila_ssd2_percent")
            ssd2_used_gb = self.get_telemetry("aquila_ssd2_used_gb")
            ssd2_total_gb = self.get_telemetry("aquila_ssd2_total_gb")
            
            cpu_temp = self.get_telemetry("aquila_cpu_temp")
            memory_percent = self.get_telemetry("aquila_memory_percent")
            
            # Check for timeouts or errors
            all_responses = [ssd1_mounted, ssd1_percent, ssd1_used_gb, ssd1_total_gb,
                           ssd2_mounted, ssd2_percent, ssd2_used_gb, ssd2_total_gb,
                           cpu_temp, memory_percent]
            
            if any("TIMEOUT" in str(resp) or "ERROR" in str(resp) for resp in all_responses):
                self.logger.warning("Some Aquila telemetry requests failed")
                self.current_data.valid = False
                return False
            
            # Parse and store the data
            try:
                self.current_data.ssd1_mounted = int(ssd1_mounted) == 1
                self.current_data.ssd1_percent = float(ssd1_percent)
                self.current_data.ssd1_used_gb = float(ssd1_used_gb)
                self.current_data.ssd1_total_gb = float(ssd1_total_gb)
                
                self.current_data.ssd2_mounted = int(ssd2_mounted) == 1
                self.current_data.ssd2_percent = float(ssd2_percent)
                self.current_data.ssd2_used_gb = float(ssd2_used_gb)
                self.current_data.ssd2_total_gb = float(ssd2_total_gb)
                
                self.current_data.cpu_temp = float(cpu_temp)
                self.current_data.memory_percent = float(memory_percent)
                
                self.current_data.last_update_time = time.time()
                self.current_data.valid = True
                self.consecutive_failures = 0
                
                self.logger.debug(f"Aquila data updated - CPU: {self.current_data.cpu_temp}°C, "
                                f"SSD1: {self.current_data.ssd1_percent}%, "
                                f"SSD2: {self.current_data.ssd2_percent}%")
                return True
                
            except (ValueError, TypeError) as e:
                self.logger.error(f"Failed to parse Aquila telemetry data: {e}")
                self.current_data.valid = False
                return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error updating Aquila data: {e}")
            self.current_data.valid = False
            return False
    
    def is_connected(self) -> bool:
        """Check if client is currently connected (based on recent successful data)"""
        if not self.current_data.valid:
            return False
        
        # Consider connected if we got valid data in the last 30 seconds
        time_since_update = time.time() - self.current_data.last_update_time
        return time_since_update < 30.0
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate in KB/s"""
        current_time = time.time()
        time_elapsed = current_time - self.last_rate_check
        
        if time_elapsed >= 1.0:  # Update rate calculation every second
            rate_bps = self.bytes_received / time_elapsed
            rate_kbps = rate_bps / 1024.0
            
            # Reset for next calculation
            self.bytes_received = 0
            self.last_rate_check = current_time
            
            return rate_kbps
        
        return 0.0
    
    def cleanup(self):
        """Clean up client resources"""
        self.logger.info("Aquila client cleaned up")


"""
Gyroscope Client for BVEX Ground Station
UDP client for gyroscope telemetry from BCP Sag position sensor system
"""

import socket
import time
import logging
from dataclasses import dataclass
from typing import Optional


@dataclass
class GyroData:
    """Gyroscope data structure for BCP Sag system - Single axis SPI gyroscope only"""
    # SPI Gyroscope (ADXRS453) - single axis rate gyroscope
    spi_rate: float = 0.0  # deg/s - angular velocity
    
    # System status
    pos_status: str = "N/A"
    pos_running: int = 0
    
    # Data validity
    valid: bool = False
    last_update_time: float = 0.0


class GyroClient:
    """UDP client for gyroscope telemetry from BCP Sag telemetry server"""
    
    def __init__(self, server_ip: str = "172.20.4.170", server_port: int = 8082, timeout: float = 1.0):
        self.server_ip = server_ip
        self.server_port = server_port
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Current data
        self.current_data = GyroData()
        self.last_update_time = 0.0
        
        # Connection tracking
        self.connection_attempts = 0
        self.last_connection_attempt = 0.0
        self.consecutive_failures = 0
        
        # Gyroscope telemetry channels - SPI single-axis only
        self.channels = {
            'spi_rate': 'pos_spi_gyro_rate',
            'pos_status': 'pos_status',
            'pos_running': 'pos_running'
        }
        
        self.logger.info(f"Gyro client initialized - Server: {server_ip}:{server_port}")
    
    def get_telemetry(self, channel_name: str) -> str:
        """Request specific telemetry data from gyro server"""
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
            
            return response.decode('utf-8').strip()
        
        except socket.timeout:
            self.consecutive_failures += 1
            return "TIMEOUT"
        except Exception as e:
            self.logger.debug(f"Error getting {channel_name}: {e}")
            self.consecutive_failures += 1
            return f"ERROR: {e}"
    
    def update_data(self) -> bool:
        """Update SPI gyroscope telemetry data"""
        try:
            # Update connection tracking
            self.connection_attempts += 1
            self.last_connection_attempt = time.time()
            
            # Fetch SPI gyro rate (primary data)
            spi_result = self.get_telemetry(self.channels['spi_rate'])
            if spi_result not in ["TIMEOUT", "N/A"] and not spi_result.startswith("ERROR"):
                try:
                    self.current_data.spi_rate = float(spi_result)
                    # Update validity and timing for successful data
                    self.current_data.valid = True
                    self.current_data.last_update_time = time.time()
                    self.last_update_time = time.time()
                    self.consecutive_failures = 0
                    self.logger.debug(f"SPI Gyro rate updated: {self.current_data.spi_rate:.3f} deg/s")
                    return True
                except ValueError:
                    self.logger.debug(f"Invalid SPI gyro value: {spi_result}")
            else:
                self.logger.debug(f"SPI gyro request failed: {spi_result}")
            
            # If we get here, the update failed
            self.current_data.valid = False
            self.consecutive_failures += 1
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating gyro data: {e}")
            self.current_data.valid = False
            self.consecutive_failures += 1
            return False
    
    def get_data(self) -> GyroData:
        """Get current gyroscope data"""
        return self.current_data
    
    def get_connection_status(self) -> str:
        """Get human-readable connection status"""
        if self.consecutive_failures == 0 and self.current_data.valid:
            return "Connected"
        elif self.consecutive_failures < 3:
            return "Connecting..."
        else:
            return "Disconnected"
    
    def is_connected(self) -> bool:
        """Check if gyroscope client is connected and receiving valid data"""
        return self.current_data.valid and self.consecutive_failures == 0

"""
BCP Housekeeping Client for BVEX Ground Station
Fetches housekeeping sensor data from the BCP Ophiuchus telemetry server
"""

import socket
import logging
import time
from typing import Dict, Any, Optional


class HousekeepingData:
    """Data container for BCP housekeeping telemetry"""
    
    def __init__(self):
        self.valid = False
        self.timestamp = 0.0
        
        # System Status
        self.hk_powered = 0
        self.hk_running = 0
        
        # Temperature Sensors (°C)
        # I2C Temperature (OCXO)
        self.hk_ocxo_temp = -999.0
        
        # Analog Frontend Temperatures (LM335)
        self.hk_ifamp_temp = -999.0      # IF Amplifier temperature
        self.hk_lo_temp = -999.0         # Local Oscillator temperature
        self.hk_tec_temp = -999.0        # TEC temperature
        
        # Analog Backend Temperatures (LM335)
        self.hk_backend_chassis_temp = -999.0  # Backend Chassis temperature
        self.hk_nic_temp = -999.0              # NIC temperature
        self.hk_rfsoc_chassis_temp = -999.0    # RFSoC Chassis temperature
        self.hk_rfsoc_chip_temp = -999.0       # RFSoC Chip temperature
        
        # LNA Box Temperatures (LM335)
        self.hk_lna1_temp = -999.0       # LNA1 temperature
        self.hk_lna2_temp = -999.0       # LNA2 temperature
        
        # Pressure Sensor (bar)
        self.hk_pv_pressure_bar = -999.0  # Pump-down valve pressure in bar


class HousekeepingClient:
    """UDP client for BCP housekeeping telemetry"""
    
    def __init__(self, server_ip="127.0.0.1", server_port=8002, timeout=1.0):
        self.logger = logging.getLogger(__name__)
        self.server_ip = server_ip
        self.server_port = server_port
        self.timeout = timeout
        
        # Current data
        self.current_data = HousekeepingData()
        self.last_update_time = 0.0
        
        # Connection tracking
        self.connection_attempts = 0
        self.last_connection_attempt = 0.0
        self._last_error = ""
        
        # Housekeeping telemetry channels according to HOUSEKEEPING_CLIENT_GUIDE.md
        self.channels = [
            # System Status
            "hk_powered", "hk_running",
            
            # Temperature Sensors
            "hk_ocxo_temp",
            "hk_ifamp_temp", "hk_lo_temp", "hk_tec_temp",
            "hk_backend_chassis_temp", "hk_nic_temp", "hk_rfsoc_chassis_temp", "hk_rfsoc_chip_temp",
            "hk_lna1_temp", "hk_lna2_temp",
            
            # Pressure Sensor (only bar, as requested)
            "hk_pv_pressure_bar"
        ]
        
        self.logger.info(f"Housekeeping client initialized - Server: {server_ip}:{server_port}")
    
    def get_telemetry(self, channel_name: str) -> str:
        """Request specific telemetry data from BCP server"""
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
            return "TIMEOUT"
        except Exception as e:
            self.logger.debug(f"Error getting {channel_name}: {e}")
            return f"ERROR: {e}"
    
    def update_data(self) -> bool:
        """Update all housekeeping telemetry data"""
        try:
            current_time = time.time()
            
            # Rate limiting - don't update more than once per second
            if current_time - self.last_update_time < 1.0:
                return self.current_data.valid
            
            self.connection_attempts += 1
            self.last_connection_attempt = current_time
            
            # Fetch all channels
            data_dict = {}
            any_valid = False
            
            for channel in self.channels:
                value = self.get_telemetry(channel)
                if value not in ["TIMEOUT", "N/A"] and not value.startswith("ERROR"):
                    data_dict[channel] = value
                    any_valid = True
                else:
                    data_dict[channel] = None
                    # Store last error for status reporting
                    self._last_error = value
                    # Log errors for debugging
                    if "TIMEOUT" in value:
                        self.logger.debug(f"Timeout for {channel}")
                    elif "ERROR" in value:
                        self.logger.debug(f"Server error for {channel}: {value}")
            
            if any_valid:
                # Update data object
                self.current_data.valid = True
                self.current_data.timestamp = current_time
                
                # System Status
                try:
                    self.current_data.hk_powered = int(data_dict.get("hk_powered", 0) or 0)
                except (ValueError, TypeError):
                    self.current_data.hk_powered = 0
                
                try:
                    self.current_data.hk_running = int(data_dict.get("hk_running", 0) or 0)
                except (ValueError, TypeError):
                    self.current_data.hk_running = 0
                
                # Temperature readings with error value handling
                temperature_channels = [
                    "hk_ocxo_temp", "hk_ifamp_temp", "hk_lo_temp", "hk_tec_temp",
                    "hk_backend_chassis_temp", "hk_nic_temp", "hk_rfsoc_chassis_temp", 
                    "hk_rfsoc_chip_temp", "hk_lna1_temp", "hk_lna2_temp"
                ]
                
                for channel in temperature_channels:
                    try:
                        value = data_dict.get(channel, -999.0)
                        if value is not None:
                            setattr(self.current_data, channel, float(value))
                        else:
                            setattr(self.current_data, channel, -999.0)
                    except (ValueError, TypeError):
                        setattr(self.current_data, channel, -999.0)
                
                # Pressure reading
                try:
                    value = data_dict.get("hk_pv_pressure_bar", -999.0)
                    if value is not None:
                        self.current_data.hk_pv_pressure_bar = float(value)
                    else:
                        self.current_data.hk_pv_pressure_bar = -999.0
                except (ValueError, TypeError):
                    self.current_data.hk_pv_pressure_bar = -999.0
                
                self.last_update_time = current_time
                return True
            else:
                # No valid data received
                self.current_data.valid = False
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating housekeeping data: {e}")
            self.current_data.valid = False
            self._last_error = str(e)
            return False
    
    def is_connected(self) -> bool:
        """Check if client is successfully receiving data"""
        return self.current_data.valid and (time.time() - self.last_update_time < 10.0)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'attempts': self.connection_attempts,
            'last_attempt': self.last_connection_attempt,
            'last_update': self.last_update_time,
            'connected': self.is_connected(),
            'valid_data': self.current_data.valid,
            'last_error': self._last_error
        }
    
    def get_temperature_status(self, temp_value: float) -> str:
        """Get temperature status with color coding as per guide recommendations"""
        if temp_value == -999.0:
            return "error"  # Gray - sensor error
        elif temp_value < 0 or temp_value > 80:
            return "critical"  # Red - critical range
        elif temp_value > 60:
            return "warning"  # Yellow - warning range
        else:
            return "normal"  # Green - normal range
    
    def get_pressure_status(self, pressure_value: float) -> str:
        """Get pressure status"""
        if pressure_value == -999.0:
            return "invalid"  # Invalid reading
        elif 0 <= pressure_value <= 1.72:  # 0-25 PSI converted to bar
            return "normal"
        else:
            return "warning"
    
    def cleanup(self):
        """Cleanup resources"""
        # No persistent connections to close for UDP
        self.logger.info("Housekeeping client cleanup completed")

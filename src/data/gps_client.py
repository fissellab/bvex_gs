"""
GPS Client for BVEX Ground Station
Python implementation of the GPS data client
"""

import socket
import threading
import time
import logging
from dataclasses import dataclass
from typing import Optional
from src.config.settings import GPS_SERVER, GPS_PROCESSING

@dataclass
class GPSData:
    """GPS data structure matching the C implementation"""
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0
    head: float = 0.0
    timestamp: Optional[float] = None
    valid: bool = False

class GPSClient:
    """Thread-safe GPS client for receiving data from flight computer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gps_data = GPSData()
        self.data_lock = threading.Lock()
        self.running = False
        self.thread = None
        self.socket = None
        
    def start(self) -> bool:
        """Start the GPS client thread"""
        if self.running:
            return True
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(GPS_SERVER['timeout'])
            self.running = True
            self.thread = threading.Thread(target=self._client_loop, daemon=True)
            self.thread.start()
            self.logger.info(f"GPS client started, connecting to {GPS_SERVER['host']}:{GPS_SERVER['port']}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start GPS client: {e}")
            return False
    
    def stop(self):
        """Stop the GPS client"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join(timeout=2.0)
        self.logger.info("GPS client stopped")
    
    def get_gps_data(self) -> GPSData:
        """Get the current GPS data (thread-safe)"""
        with self.data_lock:
            return GPSData(
                lat=self.gps_data.lat,
                lon=self.gps_data.lon,
                alt=self.gps_data.alt,
                head=self.gps_data.head,
                timestamp=self.gps_data.timestamp,
                valid=self.gps_data.valid
            )
    
    def _client_loop(self):
        """Main client loop running in separate thread"""
        server_addr = (GPS_SERVER['host'], GPS_SERVER['port'])
        request_msg = GPS_SERVER['request_message'].encode('utf-8')
        
        while self.running:
            try:
                # Send GPS request
                self.socket.sendto(request_msg, server_addr)
                
                # Receive response
                data, addr = self.socket.recvfrom(1024)
                response = data.decode('utf-8')
                
                # Parse GPS data
                if self._parse_gps_data(response):
                    with self.data_lock:
                        self.gps_data.timestamp = time.time()
                        self.gps_data.valid = True
                else:
                    self.logger.warning(f"Failed to parse GPS data: {response}")
                    
            except socket.timeout:
                self.logger.warning("GPS server timeout")
                with self.data_lock:
                    self.gps_data.valid = False
            except Exception as e:
                self.logger.error(f"GPS client error: {e}")
                with self.data_lock:
                    self.gps_data.valid = False
            
            time.sleep(GPS_SERVER['update_interval'])
    
    def _parse_gps_data(self, data_string: str) -> bool:
        """Parse GPS data string in format: gps_lat:XX,gps_lon:XX,gps_alt:XX,gps_head:XX"""
        try:
            # Expected format: "gps_lat:44.224372,gps_lon:-76.498007,gps_alt:100.0,gps_head:270.0"
            parts = data_string.split(',')
            if len(parts) != 4:
                return False
            
            lat = float(parts[0].split(':')[1])
            lon = float(parts[1].split(':')[1])
            alt = float(parts[2].split(':')[1])
            head = float(parts[3].split(':')[1])
            
            # Apply offsets from configuration
            lat += GPS_PROCESSING['coordinate_offset_lat']
            lon += GPS_PROCESSING['coordinate_offset_lon']
            head += GPS_PROCESSING['heading_offset']
            
            # Normalize heading to 0-360 degrees
            head = head % 360.0
            
            with self.data_lock:
                self.gps_data.lat = lat
                self.gps_data.lon = lon
                self.gps_data.alt = alt
                self.gps_data.head = head
            
            return True
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"GPS data parsing error: {e}")
            return False 
 
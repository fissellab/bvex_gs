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
from src.data import DataRateTracker

@dataclass
class GPSData:
    """GPS data structure matching the C implementation"""
    lat: float = 0.0
    lon: float = 0.0
    alt: float = 0.0
    head: float = 0.0
    speed: float = 0.0  # GPS speed in m/s
    sats: int = 0       # Number of satellites
    timestamp: Optional[float] = None
    valid: bool = False

class GPSClient:
    """Thread-safe GPS client for receiving data from flight computer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gps_data = GPSData()
        self.data_lock = threading.Lock()
        self.running = False
        self.paused = False  # Start unpaused by default to fix connectivity issues
        self.thread = None
        self.socket = None
        
        # Data rate tracking
        self.data_rate_tracker = DataRateTracker(window_seconds=30)
        self.total_bytes_received = 0
        
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
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop()
        # Clear GPS data
        with self.data_lock:
            self.gps_data = GPSData()
        # Reset data rate tracking
        self.data_rate_tracker.reset()
        self.total_bytes_received = 0
        self.logger.info("GPS client cleaned up")
    
    def pause(self):
        """Pause GPS data requests"""
        self.paused = True
        with self.data_lock:
            self.gps_data.valid = False
        self.logger.info("GPS client paused")
    
    def resume(self):
        """Resume GPS data requests"""
        self.paused = False
        self.logger.info("GPS client resumed")
    
    def is_paused(self) -> bool:
        """Check if GPS client is paused"""
        return self.paused
    
    def get_data_rate_kbps(self) -> float:
        """Get current data rate in KB/s"""
        if self.paused or not self.running:
            return 0.0
        return self.data_rate_tracker.get_rate_kbps()
    
    def get_total_bytes_received(self) -> int:
        """Get total bytes received since start"""
        return self.total_bytes_received
    
    def get_gps_data(self) -> GPSData:
        """Get the current GPS data (thread-safe)"""
        with self.data_lock:
            return GPSData(
                lat=self.gps_data.lat,
                lon=self.gps_data.lon,
                alt=self.gps_data.alt,
                head=self.gps_data.head,
                speed=self.gps_data.speed,
                sats=self.gps_data.sats,
                timestamp=self.gps_data.timestamp,
                valid=self.gps_data.valid
            )
    
    def _client_loop(self):
        """Main client loop running in separate thread"""
        server_addr = (GPS_SERVER['host'], GPS_SERVER['port'])
        request_msg = GPS_SERVER['request_message'].encode('utf-8')
        
        while self.running:
            try:
                # Only send requests if not paused
                if not self.paused:
                    # Send GPS request
                    self.socket.sendto(request_msg, server_addr)
                    
                    # Receive response
                    data, addr = self.socket.recvfrom(1024)
                    response = data.decode('utf-8')
                    
                    # Track data rate
                    bytes_received = len(data)
                    self.data_rate_tracker.add_data(bytes_received)
                    self.total_bytes_received += bytes_received
                    
                    # Parse GPS data
                    if self._parse_gps_data(response):
                        with self.data_lock:
                            self.gps_data.timestamp = time.time()
                            # Note: validity is now set in _parse_gps_data based on whether we have real coordinates
                    else:
                        self.logger.warning(f"Failed to parse GPS data: {response}")
                        with self.data_lock:
                            self.gps_data.valid = False
                else:
                    # When paused, mark data as invalid
                    with self.data_lock:
                        self.gps_data.valid = False
                        
            except socket.timeout:
                if not self.paused:
                    self.logger.warning("GPS server timeout")
            except Exception as e:
                if not self.paused:
                    self.logger.error(f"GPS client error: {e}")
                with self.data_lock:
                    self.gps_data.valid = False
            
            time.sleep(GPS_SERVER['update_interval'])
    
    def _parse_gps_data(self, data_string: str) -> bool:
        """Parse GPS data string in format: gps_lat:XX,gps_lon:XX,gps_alt:XX,gps_head:XX,gps_speed:XX,gps_sats:XX"""
        try:
            # Expected format: "gps_lat:44.224372,gps_lon:-76.498007,gps_alt:100.0,gps_head:270.0,gps_speed:2.571,gps_sats:8"
            # But sometimes we get: "gps_lat:N/A,gps_lon:N/A,gps_alt:N/A,gps_head:52.0,gps_speed:N/A,gps_sats:N/A"
            parts = data_string.split(',')
            
            # Handle both old format (4 parts) and new format (6 parts)
            if len(parts) == 4:
                # Old format - only lat, lon, alt, head
                lat_str = parts[0].split(':')[1]
                lon_str = parts[1].split(':')[1]
                alt_str = parts[2].split(':')[1]
                head_str = parts[3].split(':')[1]
                speed_str = 'N/A'  # Default values for missing fields
                sats_str = 'N/A'
            elif len(parts) == 6:
                # New format - includes speed and sats
                lat_str = parts[0].split(':')[1]
                lon_str = parts[1].split(':')[1]
                alt_str = parts[2].split(':')[1]
                head_str = parts[3].split(':')[1]
                speed_str = parts[4].split(':')[1]
                sats_str = parts[5].split(':')[1]
            else:
                return False
            
            # Check if we have any real GPS data (not all N/A)
            has_valid_data = not all(x == 'N/A' for x in [lat_str, lon_str, alt_str, head_str])
            
            # Parse values, keeping current values if N/A
            try:
                lat = float(lat_str) if lat_str != 'N/A' else self.gps_data.lat
            except ValueError:
                lat = self.gps_data.lat
                
            try:
                lon = float(lon_str) if lon_str != 'N/A' else self.gps_data.lon
            except ValueError:
                lon = self.gps_data.lon
                
            try:
                alt = float(alt_str) if alt_str != 'N/A' else self.gps_data.alt
            except ValueError:
                alt = self.gps_data.alt
                
            try:
                head = float(head_str) if head_str != 'N/A' else self.gps_data.head
            except ValueError:
                head = self.gps_data.head
                
            try:
                speed = float(speed_str) if speed_str != 'N/A' else self.gps_data.speed
            except ValueError:
                speed = self.gps_data.speed
                
            try:
                sats = int(sats_str) if sats_str != 'N/A' else self.gps_data.sats
            except ValueError:
                sats = self.gps_data.sats
            
            # Only apply offsets if we got actual numeric values
            if lat_str != 'N/A':
                lat += GPS_PROCESSING['coordinate_offset_lat']
            if lon_str != 'N/A':
                lon += GPS_PROCESSING['coordinate_offset_lon']
            if head_str != 'N/A':
                head += GPS_PROCESSING['heading_offset']
                # Normalize heading to 0-360 degrees
                head = head % 360.0
            
            with self.data_lock:
                self.gps_data.lat = lat
                self.gps_data.lon = lon
                self.gps_data.alt = alt
                self.gps_data.head = head
                self.gps_data.speed = speed
                self.gps_data.sats = sats
                # Mark data as valid only if we have at least some real GPS coordinates
                # When all values are N/A, the data should be considered invalid
                self.gps_data.valid = has_valid_data
            
            # Only log N/A warnings occasionally to avoid spam
            if any(x == 'N/A' for x in [lat_str, lon_str, alt_str]):
                if not hasattr(self, '_last_na_warning') or time.time() - self._last_na_warning > 10:
                    self.logger.warning(f"GPS data contains N/A values: {data_string}")
                    self._last_na_warning = time.time()
            
            return True
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"GPS data parsing error: {e}")
            return False 
 
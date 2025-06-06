"""
BCP Spectrometer UDP Client
Fetches spectrum data from the BCP Spectrometer Server
"""

import socket
import time
import logging
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class SpectrumData:
    """Data class for spectrum data"""
    type: str
    timestamp: float
    points: int
    data: list
    freq_start: Optional[float] = None
    freq_end: Optional[float] = None
    baseline: Optional[float] = None
    valid: bool = True


class BCPSpectrometerClient:
    """Client for BCP Spectrometer UDP Server"""
    
    def __init__(self, server_ip: str = "100.70.234.8", server_port: int = 8081, timeout: float = 5.0):
        self.server_ip = server_ip
        self.server_port = server_port
        self.timeout = timeout
        self.last_request_time = 0.0
        self.logger = logging.getLogger(__name__)
        self.connected = False
        
    def _send_request(self, request: str) -> Optional[str]:
        """Send UDP request and return response"""
        # Respect rate limiting (1 req/sec)
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        
        try:
            sock.sendto(request.encode('utf-8'), (self.server_ip, self.server_port))
            response = sock.recv(32768).decode('utf-8')
            self.last_request_time = time.time()
            self.connected = True
            
            # Debug logging to see actual response format
            if len(response) > 200:
                self.logger.debug(f"Response received: {response[:200]}...")
            else:
                self.logger.debug(f"Response received: {response}")
                
            return response
        except socket.timeout:
            self.logger.warning(f"Request timeout after {self.timeout}s")
            self.connected = False
            return None
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            self.connected = False
            return None
        finally:
            sock.close()
    
    def get_active_spectrometer_type(self) -> str:
        """Returns 'STANDARD', '120KHZ', 'NONE', or 'ERROR'"""
        response = self._send_request("GET_SPECTRA")
        if not response:
            return "ERROR"
        
        if response.startswith("SPECTRA_STD:"):
            return "STANDARD"
        elif response.startswith("ERROR:WRONG_SPECTROMETER_TYPE:current=120KHZ"):
            return "120KHZ"
        elif response.startswith("ERROR:SPECTROMETER_NOT_RUNNING"):
            return "NONE"
        else:
            return "ERROR"
    
    def parse_standard_response(self, response: str) -> Optional[SpectrumData]:
        """Parse standard spectrum response"""
        if not response.startswith("SPECTRA_STD:"):
            return None
        
        try:
            self.logger.debug(f"Parsing standard response: {response[:100]}...")
            
            # Format: SPECTRA_STD:timestamp:1673123456.789,points:2048,data:1.234,5.678,...
            # But the actual format might be: SPECTRA_STD:1673123456.789,points:2048,data:1.234,5.678,...
            
            # Remove the SPECTRA_STD: prefix
            content = response[12:]  # Remove "SPECTRA_STD:"
            
            # Try to find timestamp - it should be the first number before the first comma
            if content.startswith("timestamp:"):
                # Format: timestamp:1673123456.789,points:2048,data:...
                parts = content.split(',', 1)
                timestamp_part = parts[0]
                timestamp = float(timestamp_part.split(':')[1])
                metadata_and_data = parts[1] if len(parts) > 1 else ""
            else:
                # Format: 1673123456.789,points:2048,data:...
                parts = content.split(',', 1)
                timestamp = float(parts[0])
                metadata_and_data = parts[1] if len(parts) > 1 else ""
            
            # Find the data section
            data_start = metadata_and_data.find('data:')
            if data_start == -1:
                self.logger.error("No 'data:' section found in response")
                return None
            
            # Extract metadata part
            metadata_part = metadata_and_data[:data_start].rstrip(',')
            
            # Parse points from metadata
            points = None
            for item in metadata_part.split(','):
                if 'points:' in item:
                    points = int(item.split(':')[1])
                    break
            
            if points is None:
                self.logger.error("No 'points:' found in metadata")
                return None
            
            # Extract data
            data_str = metadata_and_data[data_start + 5:]  # Skip 'data:'
            data = [float(x) for x in data_str.split(',') if x.strip()]
            
            self.logger.debug(f"Successfully parsed: timestamp={timestamp}, points={points}, data_len={len(data)}")
            
            return SpectrumData(
                type='STANDARD',
                timestamp=timestamp,
                points=points,
                data=data,
                valid=True
            )
        except Exception as e:
            self.logger.error(f"Error parsing standard response: {e}")
            self.logger.error(f"Response was: {response[:200]}...")
            return None
    
    def parse_120khz_response(self, response: str) -> Optional[SpectrumData]:
        """Parse 120kHz spectrum response"""
        if not response.startswith("SPECTRA_120KHZ:"):
            return None
        
        try:
            self.logger.debug(f"Parsing 120kHz response: {response[:100]}...")
            
            # Format: SPECTRA_120KHZ:timestamp:1673123456.789,points:167,freq_start:22.225,freq_end:22.245,baseline:-45.2,data:1.234,5.678,...
            # But the actual format might be: SPECTRA_120KHZ:1673123456.789,points:167,freq_start:22.225,freq_end:22.245,baseline:-45.2,data:1.234,5.678,...
            
            # Remove the SPECTRA_120KHZ: prefix
            content = response[15:]  # Remove "SPECTRA_120KHZ:"
            
            # Try to find timestamp - it should be the first number before the first comma
            if content.startswith("timestamp:"):
                # Format: timestamp:1673123456.789,points:167,freq_start:22.225,...
                parts = content.split(',', 1)
                timestamp_part = parts[0]
                timestamp = float(timestamp_part.split(':')[1])
                metadata_and_data = parts[1] if len(parts) > 1 else ""
            else:
                # Format: 1673123456.789,points:167,freq_start:22.225,...
                parts = content.split(',', 1)
                timestamp = float(parts[0])
                metadata_and_data = parts[1] if len(parts) > 1 else ""
            
            # Find the data section
            data_start = metadata_and_data.find('data:')
            if data_start == -1:
                self.logger.error("No 'data:' section found in 120kHz response")
                return None
            
            # Extract metadata part
            metadata_part = metadata_and_data[:data_start].rstrip(',')
            
            # Parse metadata
            points = None
            freq_start = None
            freq_end = None
            baseline = None
            
            for item in metadata_part.split(','):
                if 'points:' in item:
                    points = int(item.split(':')[1])
                elif 'freq_start:' in item:
                    freq_start = float(item.split(':')[1])
                elif 'freq_end:' in item:
                    freq_end = float(item.split(':')[1])
                elif 'baseline:' in item:
                    baseline = float(item.split(':')[1])
            
            if any(x is None for x in [points, freq_start, freq_end, baseline]):
                self.logger.error(f"Missing metadata: points={points}, freq_start={freq_start}, freq_end={freq_end}, baseline={baseline}")
                return None
            
            # Extract data
            data_str = metadata_and_data[data_start + 5:]  # Skip 'data:'
            data = [float(x) for x in data_str.split(',') if x.strip()]
            
            self.logger.debug(f"Successfully parsed 120kHz: timestamp={timestamp}, points={points}, data_len={len(data)}")
            
            return SpectrumData(
                type='120KHZ',
                timestamp=timestamp,
                points=points,
                data=data,
                freq_start=freq_start,
                freq_end=freq_end,
                baseline=baseline,
                valid=True
            )
        except Exception as e:
            self.logger.error(f"Error parsing 120kHz response: {e}")
            self.logger.error(f"Response was: {response[:200]}...")
            return None
    
    def get_standard_spectrum(self) -> Optional[SpectrumData]:
        """Get standard resolution spectrum (2048 points)"""
        response = self._send_request("GET_SPECTRA")
        if not response:
            return SpectrumData(type='STANDARD', timestamp=time.time(), points=0, data=[], valid=False)
        
        if response.startswith("ERROR:"):
            self.logger.warning(f"Server error: {response}")
            return SpectrumData(type='STANDARD', timestamp=time.time(), points=0, data=[], valid=False)
        
        result = self.parse_standard_response(response)
        if result is None:
            return SpectrumData(type='STANDARD', timestamp=time.time(), points=0, data=[], valid=False)
        
        return result
    
    def get_120khz_spectrum(self) -> Optional[SpectrumData]:
        """Get high-resolution water maser spectrum (~167 points)"""
        response = self._send_request("GET_SPECTRA_120KHZ")
        if not response:
            return SpectrumData(type='120KHZ', timestamp=time.time(), points=0, data=[], valid=False)
        
        if response.startswith("ERROR:"):
            self.logger.warning(f"Server error: {response}")
            return SpectrumData(type='120KHZ', timestamp=time.time(), points=0, data=[], valid=False)
        
        result = self.parse_120khz_response(response)
        if result is None:
            return SpectrumData(type='120KHZ', timestamp=time.time(), points=0, data=[], valid=False)
        
        return result
    
    def get_spectrum(self) -> Optional[SpectrumData]:
        """Automatically get the appropriate spectrum based on active spectrometer"""
        spec_type = self.get_active_spectrometer_type()
        
        if spec_type == "STANDARD":
            return self.get_standard_spectrum()
        elif spec_type == "120KHZ":
            return self.get_120khz_spectrum()
        elif spec_type == "NONE":
            self.logger.info("No spectrometer is currently running")
            return SpectrumData(type='NONE', timestamp=time.time(), points=0, data=[], valid=False)
        else:
            self.logger.error("Error determining spectrometer type")
            return SpectrumData(type='ERROR', timestamp=time.time(), points=0, data=[], valid=False)
    
    def is_connected(self) -> bool:
        """Check if client is connected to server"""
        return self.connected 
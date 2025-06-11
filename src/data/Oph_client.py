"""
Client for Ophiuchus on the BVEX Ground Station
"""

import socket
import threading
import time
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from src.config.settings import OPH_SERVER
from src.data import DataRateTracker

@dataclass
class OphData:
    """ data structure for the star camera data"""
    sc_ra: float = 0.0  # Right Ascension
    sc_dec: float = 0.0  # Declination
    sc_fr: float = 0.0  # Field rotation
    sc_ir: float = 0.0  # Image rotation
    sc_az: float = 0.0  # Azimuth
    sc_alt: float = 0.0  # Altitude
    sc_texp: float = 0.0  # texp
    sc_start_focus: int = 0  # auto focus start position
    sc_end_focus: int = 0  # auto focus end position
    sc_curr_focus: int = 0  # current focus position
    sc_focus_step: int = 0  # auto focus stepsize
    sc_focus_mode: int = 0  # 1 if auto-focusing 0 otherwise
    sc_solve: int = 0  # 1 if solving 0 if simply taking images should only be considered when focus_mode = 0
    valid: bool = False  # indicates if data is valid

class OphClient:
    """Client for communicating with Ophiuchus star camera telemetry server"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.oph_data = OphData()
        self.data_lock = threading.Lock()
        self.running = False
        self.paused = True
        self.thread = None
        self.socket = None

        # Data rate tracking
        self.data_rate_tracker = DataRateTracker(window_seconds=30)
        self.total_bytes_received = 0

    def start(self) -> bool:
        """Start the Oph client thread"""
        if self.running:
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(OPH_SERVER['timeout'])
            self.running = True
            self.thread = threading.Thread(target=self._client_loop, daemon=True)
            self.thread.start()
            self.logger.info(f"Oph client started, connecting to {OPH_SERVER['host']}:{OPH_SERVER['port']}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Oph client: {e}")
            return False

    def stop(self):
        """Stop the client"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join(timeout=2.0)
        self.logger.info("Oph client stopped")

    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop()
        # Clear all data
        with self.data_lock:
            self.oph_data = OphData()
        # Reset data rate tracking
        self.data_rate_tracker.reset()
        self.total_bytes_received = 0
        self.logger.info("Oph client cleaned up")

    def pause(self):
        """Pause data requests"""
        self.paused = True
        with self.data_lock:
            self.oph_data.valid = False
        self.logger.info("Oph client paused")

    def resume(self):
        """Resume data requests"""
        self.paused = False
        self.logger.info("Oph client resumed")

    def get_data_rate_kbps(self) -> float:
        """Get current data rate in KB/s"""
        if self.paused or not self.running:
            return 0.0
        return self.data_rate_tracker.get_rate_kbps()

    def get_total_bytes_received(self) -> int:
        """Get total bytes received since start"""
        return self.total_bytes_received

    def get_data(self) -> OphData:
        """Get the current Star Camera data (thread-safe)"""
        with self.data_lock:
            return OphData(
                sc_ra=self.oph_data.sc_ra,
                sc_dec=self.oph_data.sc_dec,
                sc_fr=self.oph_data.sc_fr,
                sc_ir=self.oph_data.sc_ir,
                sc_az=self.oph_data.sc_az,
                sc_alt=self.oph_data.sc_alt,
                sc_texp=self.oph_data.sc_texp,
                sc_start_focus=self.oph_data.sc_start_focus,
                sc_end_focus=self.oph_data.sc_end_focus,
                sc_curr_focus=self.oph_data.sc_curr_focus,
                sc_focus_step=self.oph_data.sc_focus_step,
                sc_focus_mode=self.oph_data.sc_focus_mode,
                sc_solve=self.oph_data.sc_solve,
                valid=self.oph_data.valid
            )

    def is_connected(self) -> bool:
        """Check if client is connected and receiving valid data"""
        with self.data_lock:
            return self.running and not self.paused and self.oph_data.valid

    def _client_loop(self):
        """Main client loop"""
        server_addr = (OPH_SERVER['host'], OPH_SERVER['port'])
        request_msgs = ["sc_ra", "sc_dec", "sc_fr", "sc_ir", "sc_alt", "sc_az", "sc_texp", 
                       "sc_start_focus", "sc_end_focus", "sc_curr_focus", "sc_focus_step", 
                       "sc_focus_mode", "sc_solve"]
        types = ["float", "float", "float", "float", "float", "float", "float",
                "int", "int", "int", "int", "int", "int"]

        while self.running:
            try:
                # Only send requests if not paused
                if not self.paused:
                    temp_data = {}
                    all_successful = True
                    
                    # Loop through all metrics
                    for request_msg, data_type in zip(request_msgs, types):
                        try:
                            # Send request
                            self.logger.debug(f"Sending request '{request_msg}' to {server_addr}")
                            self.socket.sendto(request_msg.encode('utf-8'), server_addr)

                            # Receive response
                            data, addr = self.socket.recvfrom(1024)
                            response = data.decode('utf-8').strip()
                            self.logger.debug(f"Received response for '{request_msg}': '{response}' from {addr}")

                            # Track data rate
                            bytes_received = len(data)
                            self.data_rate_tracker.add_data(bytes_received)
                            self.total_bytes_received += bytes_received

                            # Parse and store data temporarily
                            try:
                                if data_type == "float":
                                    parsed_value = float(response)
                                    temp_data[request_msg] = parsed_value
                                    self.logger.debug(f"Parsed {request_msg} as float: {parsed_value}")
                                elif data_type == "int":
                                    parsed_value = int(response)
                                    temp_data[request_msg] = parsed_value
                                    self.logger.debug(f"Parsed {request_msg} as int: {parsed_value}")
                            except (ValueError, TypeError) as parse_error:
                                self.logger.warning(f"Failed to parse {request_msg}: '{response}' - {parse_error}")
                                all_successful = False
                                break
                                
                        except socket.timeout:
                            self.logger.warning(f"Timeout requesting {request_msg} from {server_addr}")
                            all_successful = False
                            break
                        except Exception as req_error:
                            self.logger.error(f"Error requesting {request_msg} from {server_addr}: {req_error}")
                            all_successful = False
                            break

                    # Update data if all requests were successful
                    if all_successful and temp_data:
                        with self.data_lock:
                            for key, value in temp_data.items():
                                setattr(self.oph_data, key, value)
                            self.oph_data.valid = True
                    else:
                        # Mark data as invalid if any request failed
                        with self.data_lock:
                            self.oph_data.valid = False

                else:
                    # If paused, mark data as invalid
                    with self.data_lock:
                        self.oph_data.valid = False

            except socket.timeout:
                if not self.paused:
                    self.logger.warning("Server timeout")
                with self.data_lock:
                    self.oph_data.valid = False
            except Exception as e:
                if not self.paused:
                    self.logger.error(f"Client error: {e}")
                with self.data_lock:
                    self.oph_data.valid = False
                    
            time.sleep(OPH_SERVER['update_interval'])

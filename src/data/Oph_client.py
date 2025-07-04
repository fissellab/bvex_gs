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
    sc_save: int = 0  # 1 if star camera is recording 0 otherwise
    mc_curr: float = 0.0  # Motor Current (A)
    mc_sw: int = 0  # Motor Status Word
    mc_lf: int = 0  # Motor Fault register
    mc_sr: int = 0  # Motor Status register
    mc_pos: float = 0.0  # Motor position (deg)
    mc_temp: int = 0  # Motor Controller Temperature (Celsius)
    mc_vel: float = 0.0  # Motor velocity (deg/s)
    mc_cwr: int = 0  # control word read
    mc_cww: int = 0  # control word write
    mc_np: int = 0  # network status
    mc_pt: float = 0.0  # Motor P term
    mc_it: float = 0.0  # Motor I term
    mc_dt: float = 0.0  # Motor D term
    ax_mode: int = 0  # 0 for velocity and 1 for position
    ax_dest: float = 0.0  # target elevation
    ax_vel: float = 0.0  # target velocity
    ax_dest_az: float = 0.0  # target azimuth
    ax_vel_az: float = 0.0  # target velocity
    ax_ot: int = 0  # 1 if on target 0 otherwise
    scan_mode: int = 0  # 0 if None 1 for elevation dither 2 for tracking 3 for elevation on-off
    scan_start: float = 0.0  # start elevation for a single dither scan
    scan_stop: float = 0.0  # stop elevation for a single dither scan
    scan_vel: float = 0.0  # scan velocity
    scan_scan: int = 0  # current scan
    scan_nscans: int = 0  # number of scans to do
    scan_offset: float = 0.0  # distance to 'off' position
    scan_op: int = 0  # -1 if on 'off' position 1 if on 'on' position and 0 if moving
    scan_time: float = 0.0  # 'on' time
    target_lon: float = 0.0  # Target coordinate longitude (e.g. RA)
    target_lat: float = 0.0  # Target coordinate latitude (e.g. DEC)
    target_type: str = "None"  # Target coordinate type (eg. RaDec)
    # PBoB relay states and current measurements
    sc_state: int = 0  # Star camera relay state (0=OFF, 1=ON)
    sc_curr: float = 0.0  # Star camera current (A)
    m_state: int = 0  # Motor relay state (0=OFF, 1=ON)
    m_curr: float = 0.0  # Motor current (A)
    gps_state: int = 0  # GPS relay state (0=OFF, 1=ON) - connected to relay 2 of PBoB 1
    gps_curr: float = 0.0  # GPS current (A) - connected to relay 2 of PBoB 1
    lp_state: int = 0  # Lock pin relay state (0=OFF, 1=ON)
    lp_curr: float = 0.0  # Lock pin current (A)
    lna_state: int = 0  # LNA relay state (0=OFF, 1=ON)
    lna_curr: float = 0.0  # LNA current (A)
    mix_state: int = 0  # Mixer relay state (0=OFF, 1=ON)
    mix_curr: float = 0.0  # Mixer current (A)
    rfsoc_state: int = 0  # RF SoC relay state (0=OFF, 1=ON)
    rfsoc_curr: float = 0.0  # RF SoC current (A)
    valid: bool = False  # indicates if data is valid

class OphClient:
    """Client for communicating with Ophiuchus star camera telemetry server"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.oph_data = OphData()
        self.data_lock = threading.Lock()
        self.running = False
        self.paused = False  # Start unpaused so data flows immediately
        self.thread = None
        self.socket = None

        # Data rate tracking
        self.data_rate_tracker = DataRateTracker(window_seconds=30)
        self.total_bytes_received = 0

    def start(self) -> bool:
        """Start the Oph client thread"""
        if self.running:
            self.logger.debug("OphClient already running")
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(OPH_SERVER['timeout'])
            self.running = True
            self.thread = threading.Thread(target=self._client_loop, daemon=True)
            self.thread.start()
            self.logger.info(f"Oph client started successfully")
            self.logger.debug(f"Connecting to {OPH_SERVER['host']}:{OPH_SERVER['port']}")
            self.logger.debug(f"Timeout: {OPH_SERVER['timeout']}s, Update interval: {OPH_SERVER['update_interval']}s")
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
        self.logger.debug("Oph client stopped")

    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop()
        # Clear all data
        with self.data_lock:
            self.oph_data = OphData()
        # Reset data rate tracking
        self.data_rate_tracker.reset()
        self.total_bytes_received = 0
        self.logger.debug("Oph client cleaned up")

    def pause(self):
        """Pause data requests"""
        self.paused = True
        with self.data_lock:
            self.oph_data.valid = False
        self.logger.debug("Oph client paused - stopping data requests")

    def resume(self):
        """Resume data requests"""
        self.paused = False
        self.logger.debug("Oph client resumed - starting data requests")
    
    def is_paused(self) -> bool:
        """Check if client is paused"""
        return self.paused

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
                sc_save=self.oph_data.sc_save,
                mc_curr=self.oph_data.mc_curr,
                mc_sw=self.oph_data.mc_sw,
                mc_lf=self.oph_data.mc_lf,
                mc_sr=self.oph_data.mc_sr,
                mc_pos=self.oph_data.mc_pos,
                mc_temp=self.oph_data.mc_temp,
                mc_vel=self.oph_data.mc_vel,
                mc_cwr=self.oph_data.mc_cwr,
                mc_cww=self.oph_data.mc_cww,
                mc_np=self.oph_data.mc_np,
                mc_pt=self.oph_data.mc_pt,
                mc_it=self.oph_data.mc_it,
                mc_dt=self.oph_data.mc_dt,
                ax_mode=self.oph_data.ax_mode,
                ax_dest=self.oph_data.ax_dest,
                ax_vel=self.oph_data.ax_vel,
                ax_dest_az=self.oph_data.ax_dest_az,
                ax_vel_az=self.oph_data.ax_vel_az,
                ax_ot=self.oph_data.ax_ot,
                scan_mode=self.oph_data.scan_mode,
                scan_start=self.oph_data.scan_start,
                scan_stop=self.oph_data.scan_stop,
                scan_vel=self.oph_data.scan_vel,
                scan_scan=self.oph_data.scan_scan,
                scan_nscans=self.oph_data.scan_nscans,
                scan_offset=self.oph_data.scan_offset,
                scan_op=self.oph_data.scan_op,
                scan_time=self.oph_data.scan_time,
                target_lon=self.oph_data.target_lon,
                target_lat=self.oph_data.target_lat,
                target_type=self.oph_data.target_type,
                sc_state=self.oph_data.sc_state,
                sc_curr=self.oph_data.sc_curr,
                m_state=self.oph_data.m_state,
                m_curr=self.oph_data.m_curr,
                gps_state=self.oph_data.gps_state,
                gps_curr=self.oph_data.gps_curr,
                lp_state=self.oph_data.lp_state,
                lp_curr=self.oph_data.lp_curr,
                lna_state=self.oph_data.lna_state,
                lna_curr=self.oph_data.lna_curr,
                mix_state=self.oph_data.mix_state,
                mix_curr=self.oph_data.mix_curr,
                rfsoc_state=self.oph_data.rfsoc_state,
                rfsoc_curr=self.oph_data.rfsoc_curr,
                valid=self.oph_data.valid
            )

    def is_connected(self) -> bool:
        """Check if client is connected and receiving valid data"""
        with self.data_lock:
            return self.running and not self.paused and self.oph_data.valid

    def _client_loop(self):
        """Main client loop running in separate thread"""
        # Define all parameters to request with their expected types
        request_msgs = ['sc_ra', 'sc_dec', 'sc_fr', 'sc_ir', 'sc_az', 'sc_alt', 'sc_texp',
                       'sc_start_focus', 'sc_end_focus', 'sc_curr_focus', 'sc_focus_step',
                       'sc_focus_mode', 'sc_solve', 'sc_save',
                       'mc_curr', 'mc_sw', 'mc_lf', 'mc_sr', 'mc_pos', 'mc_temp', 'mc_vel', 
                       'mc_cwr', 'mc_cww', 'mc_np', 'mc_pt', 'mc_it', 'mc_dt',
                       'ax_mode', 'ax_dest', 'ax_vel', 'ax_dest_az', 'ax_vel_az', 'ax_ot',
                       'scan_mode', 'scan_start', 'scan_stop', 'scan_vel', 'scan_scan', 'scan_nscans', 'scan_offset', 'scan_op', 'scan_time',
                       'target_lon', 'target_lat', 'target_type',
                       'sc_state', 'sc_curr', 'm_state', 'm_curr', 'gps_state', 'gps_curr',
                       'lp_state', 'lp_curr', 'lna_state', 'lna_curr', 'mix_state', 'mix_curr', 'rfsoc_state', 'rfsoc_curr']
        
        types = [float, float, float, float, float, float, float,
                 int, int, int, int,
                 int, int, int,
                 float, int, int, int, float, int, float,
                 int, int, int, float, float, float,
                 int, float, float, float, float, int,
                 int, float, float, float, int, int, float, int, float,
                 float, float, str,
                 int, float, int, float, int, float,
                 int, float, int, float, int, float, int, float]
        
        server_addr = (OPH_SERVER['host'], OPH_SERVER['port'])
        self.logger.debug(f"Parameters to request: {request_msgs}")
        self.logger.debug(f"Timeout: {OPH_SERVER['timeout']}s, Update interval: {OPH_SERVER['update_interval']}s")

        while self.running:
            try:
                # Only send requests if not paused
                if not self.paused:
                    temp_data = {}
                    all_successful = True
                    
                    self.logger.debug(f"Starting request cycle for {len(request_msgs)} parameters")
                    
                    # Loop through all metrics
                    for i, (request_msg, data_type) in enumerate(zip(request_msgs, types)):
                        try:
                            # Use shorter timeout for individual requests, especially for problematic ones
                            if request_msg in ['gps_state', 'gps_curr']:
                                # These parameters seem to timeout frequently, use shorter timeout
                                original_timeout = self.socket.gettimeout()
                                self.socket.settimeout(2.0)  # 2 second timeout for GPS-related requests
                            
                            # Send request
                            self.logger.debug(f"[{i+1}/{len(request_msgs)}] Sending request '{request_msg}' (type: {data_type}) to {server_addr}")
                            self.socket.sendto(request_msg.encode('utf-8'), server_addr)

                            # Receive response
                            data, addr = self.socket.recvfrom(1024)
                            response = data.decode('utf-8').strip()
                            self.logger.debug(f"[{i+1}/{len(request_msgs)}] Received response for '{request_msg}': '{response}' from {addr}")

                            # Track data rate
                            bytes_received = len(data)
                            self.data_rate_tracker.add_data(bytes_received)
                            self.total_bytes_received += bytes_received

                            # Parse response based on type
                            try:
                                if data_type == float:
                                    value = float(response)
                                    self.logger.debug(f"Parsed {request_msg} as float: {value}")
                                elif data_type == int:
                                    value = int(response)
                                    self.logger.debug(f"Parsed {request_msg} as int: {value}")
                                elif data_type == str:
                                    value = response
                                    self.logger.debug(f"Parsed {request_msg} as str: {value}")
                                else:
                                    self.logger.warning(f"Unknown data type for {request_msg}: {data_type}")
                                    continue
                                
                                temp_data[request_msg] = value
                                
                            except ValueError as e:
                                self.logger.warning(f"Failed to parse {request_msg} response '{response}': {e}")
                                all_successful = False
                            
                            # Restore original timeout if it was changed
                            if request_msg in ['gps_state', 'gps_curr']:
                                self.socket.settimeout(original_timeout)

                        except socket.timeout:
                            if request_msg in ['gps_state', 'gps_curr']:
                                # Don't log warnings for GPS-related timeouts, they're common
                                self.logger.debug(f"Timeout requesting {request_msg} from {server_addr} (expected for GPS parameters)")
                                # Set default values for GPS parameters
                                if request_msg == 'gps_state':
                                    temp_data[request_msg] = 0  # Default to OFF
                                elif request_msg == 'gps_curr':
                                    temp_data[request_msg] = 0.0  # Default to 0 current
                                # Restore timeout
                                self.socket.settimeout(original_timeout)
                            else:
                                self.logger.debug(f"Timeout requesting {request_msg} from {server_addr}")
                                all_successful = False
                        except Exception as e:
                            self.logger.debug(f"Error requesting {request_msg}: {e}")
                            all_successful = False

                    # Update the data structure with all successful values
                    if temp_data:  # If we got at least some data
                        with self.data_lock:
                            # Update all successfully received values
                            for param, value in temp_data.items():
                                if hasattr(self.oph_data, param):
                                    setattr(self.oph_data, param, value)
                            
                            # Mark data as valid if we got most of the important parameters
                            # Consider data valid if we got motor, star camera, and PBOB data (even if GPS times out)
                            critical_params = ['mc_curr', 'sc_state', 'sc_curr', 'm_state', 'm_curr']
                            critical_received = sum(1 for param in critical_params if param in temp_data)
                            
                            if critical_received >= 4:  # If we got at least 4 out of 5 critical parameters
                                self.oph_data.valid = True
                                self.logger.debug(f"Data marked as valid - received {len(temp_data)}/{len(request_msgs)} parameters including {critical_received}/{len(critical_params)} critical ones")
                            else:
                                self.oph_data.valid = False
                                self.logger.debug(f"Data marked invalid - only received {critical_received}/{len(critical_params)} critical parameters")
                    else:
                        with self.data_lock:
                            self.oph_data.valid = False
                        self.logger.debug("No data received - marking invalid")

                else:
                    # If paused, mark data as invalid
                    with self.data_lock:
                        self.oph_data.valid = False
                    self.logger.debug("Client paused - data marked invalid")

            except socket.timeout:
                if not self.paused:
                    self.logger.debug("Server timeout in main loop")
                with self.data_lock:
                    self.oph_data.valid = False
            except Exception as e:
                if not self.paused:
                    self.logger.debug(f"Client error in main loop: {e}")
                with self.data_lock:
                    self.oph_data.valid = False
                    
            time.sleep(OPH_SERVER['update_interval'])

    def get_debug_info(self) -> dict:
        """Get debugging information about the client state"""
        with self.data_lock:
            return {
                'running': self.running,
                'paused': self.paused,
                'data_valid': self.oph_data.valid,
                'total_bytes': self.total_bytes_received,
                'data_rate_kbps': self.get_data_rate_kbps(),
                'sample_data': {
                    'sc_ra': self.oph_data.sc_ra,
                    'sc_dec': self.oph_data.sc_dec,
                    'sc_az': self.oph_data.sc_az,
                    'sc_alt': self.oph_data.sc_alt,
                    'mc_curr': self.oph_data.mc_curr,
                    'mc_pos': self.oph_data.mc_pos,
                    'target_type': self.oph_data.target_type,
                    'pbob_data': {
                        'sc_state': self.oph_data.sc_state,
                        'sc_curr': self.oph_data.sc_curr,
                        'm_state': self.oph_data.m_state,
                        'm_curr': self.oph_data.m_curr,
                        'lna_state': self.oph_data.lna_state,
                        'lna_curr': self.oph_data.lna_curr
                    }
                }
            }

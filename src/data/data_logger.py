"""
Comprehensive Data Logger for BVEX Ground Station
Logs star camera telemetry, motor operations, scanning operations, and spectrometer timestamps
"""

import csv
import os
import time
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import fields


class DataLogger:
    """Background data logger for BCP operations"""
    
    def __init__(self, main_window):
        """Initialize with reference to main window to access all widgets"""
        self.main_window = main_window
        self.logger = logging.getLogger(__name__)
        
        # Logging state
        self.is_logging = False
        self.log_thread = None
        self.log_file_path = None
        self.csv_writer = None
        self.csv_file = None
        
        # Thread control
        self.stop_event = threading.Event()
        self.data_lock = threading.Lock()
        
        # Logging interval (1 Hz max)
        self.log_interval = 1.0  # seconds
        
        # Create logs directory if it doesn't exist
        self.logs_dir = 'logs'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            
    def get_csv_headers(self) -> list:
        """Get CSV headers for all logged data"""
        headers = ['timestamp', 'datetime_utc']
        
        # Star camera telemetry headers
        star_cam_headers = [
            'sc_ra', 'sc_dec', 'sc_fr', 'sc_ir', 'sc_az', 'sc_alt', 'sc_texp',
            'sc_start_focus', 'sc_end_focus', 'sc_curr_focus', 'sc_focus_step',
            'sc_focus_mode', 'sc_solve', 'sc_save'
        ]
        headers.extend(star_cam_headers)
        
        # Motor controller headers
        motor_headers = [
            'mc_curr', 'mc_sw', 'mc_lf', 'mc_sr', 'mc_pos', 'mc_temp', 'mc_vel',
            'mc_cwr', 'mc_cww', 'mc_np', 'mc_pt', 'mc_it', 'mc_dt'
        ]
        headers.extend(motor_headers)
        
        # Motor/axis operation headers  
        axis_headers = [
            'ax_mode', 'ax_dest', 'ax_vel', 'ax_dest_az', 'ax_vel_az', 'ax_ot'
        ]
        headers.extend(axis_headers)
        
        # Scanning operation headers
        scan_headers = [
            'scan_mode', 'scan_start', 'scan_stop', 'scan_vel', 'scan_scan',
            'scan_nscans', 'scan_offset', 'scan_op'
        ]
        headers.extend(scan_headers)
        
        # Target coordinate headers
        target_headers = ['target_lon', 'target_lat', 'target_type']
        headers.extend(target_headers)
        
        # Spectrometer headers (timestamps only)
        spectrometer_headers = [
            'spec_timestamp', 'spec_type', 'spec_points', 'spec_valid'
        ]
        headers.extend(spectrometer_headers)
        
        # Data validity headers
        validity_headers = ['oph_data_valid', 'spec_data_valid']
        headers.extend(validity_headers)
        
        return headers
    
    def collect_data_row(self) -> Dict[str, Any]:
        """Collect a single row of data from all sources via GUI widgets"""
        current_timestamp = time.time()
        current_datetime = datetime.utcfromtimestamp(current_timestamp).isoformat() + 'Z'
        
        # Initialize row with timestamp
        row = {
            'timestamp': current_timestamp,
            'datetime_utc': current_datetime
        }
        
        # Collect Oph data (star camera telemetry, motor data, scanning ops) from GUI widgets
        try:
            # Get data from the shared OphClient via GUI widgets instead of making our own calls
            oph_data = None
            oph_data_valid = False
            
            # Try to get telemetry from active widgets
            if hasattr(self.main_window, 'star_camera_widget') and self.main_window.star_camera_widget.is_star_camera_active():
                oph_data = self.main_window.star_camera_widget.get_current_telemetry()
                oph_data_valid = oph_data.valid if oph_data else False
            elif hasattr(self.main_window, 'motor_controller_widget') and self.main_window.motor_controller_widget.is_motor_controller_active():
                oph_data = self.main_window.motor_controller_widget.get_current_telemetry()
                oph_data_valid = oph_data.valid if oph_data else False
            elif hasattr(self.main_window, 'scanning_operations_widget') and self.main_window.scanning_operations_widget.is_scanning_operations_active():
                oph_data = self.main_window.scanning_operations_widget.get_current_telemetry()
                oph_data_valid = oph_data.valid if oph_data else False
            
            if oph_data and oph_data_valid:
                # Star camera telemetry
                row.update({
                    'sc_ra': oph_data.sc_ra,
                    'sc_dec': oph_data.sc_dec,
                    'sc_fr': oph_data.sc_fr,
                    'sc_ir': oph_data.sc_ir,
                    'sc_az': oph_data.sc_az,
                    'sc_alt': oph_data.sc_alt,
                    'sc_texp': oph_data.sc_texp,
                    'sc_start_focus': oph_data.sc_start_focus,
                    'sc_end_focus': oph_data.sc_end_focus,
                    'sc_curr_focus': oph_data.sc_curr_focus,
                    'sc_focus_step': oph_data.sc_focus_step,
                    'sc_focus_mode': oph_data.sc_focus_mode,
                    'sc_solve': oph_data.sc_solve,
                    'sc_save': oph_data.sc_save
                })
                
                # Motor controller data
                row.update({
                    'mc_curr': oph_data.mc_curr,
                    'mc_sw': oph_data.mc_sw,
                    'mc_lf': oph_data.mc_lf,
                    'mc_sr': oph_data.mc_sr,
                    'mc_pos': oph_data.mc_pos,
                    'mc_temp': oph_data.mc_temp,
                    'mc_vel': oph_data.mc_vel,
                    'mc_cwr': oph_data.mc_cwr,
                    'mc_cww': oph_data.mc_cww,
                    'mc_np': oph_data.mc_np,
                    'mc_pt': oph_data.mc_pt,
                    'mc_it': oph_data.mc_it,
                    'mc_dt': oph_data.mc_dt
                })
                
                # Axis operation data
                row.update({
                    'ax_mode': oph_data.ax_mode,
                    'ax_dest': oph_data.ax_dest,
                    'ax_vel': oph_data.ax_vel,
                    'ax_dest_az': oph_data.ax_dest_az,
                    'ax_vel_az': oph_data.ax_vel_az,
                    'ax_ot': oph_data.ax_ot
                })
                
                # Scanning operation data
                row.update({
                    'scan_mode': oph_data.scan_mode,
                    'scan_start': oph_data.scan_start,
                    'scan_stop': oph_data.scan_stop,
                    'scan_vel': oph_data.scan_vel,
                    'scan_scan': oph_data.scan_scan,
                    'scan_nscans': oph_data.scan_nscans,
                    'scan_offset': oph_data.scan_offset,
                    'scan_op': oph_data.scan_op
                })
                
                # Target coordinate data
                row.update({
                    'target_lon': oph_data.target_lon,
                    'target_lat': oph_data.target_lat,
                    'target_type': oph_data.target_type
                })
                
                row['oph_data_valid'] = True
            else:
                # Fill with default/empty values when no data available
                for key in ['sc_ra', 'sc_dec', 'sc_fr', 'sc_ir', 'sc_az', 'sc_alt', 'sc_texp',
                           'sc_start_focus', 'sc_end_focus', 'sc_curr_focus', 'sc_focus_step',
                           'sc_focus_mode', 'sc_solve', 'sc_save', 'mc_curr', 'mc_sw', 'mc_lf',
                           'mc_sr', 'mc_pos', 'mc_temp', 'mc_vel', 'mc_cwr', 'mc_cww', 'mc_np',
                           'mc_pt', 'mc_it', 'mc_dt', 'ax_mode', 'ax_dest', 'ax_vel', 'ax_dest_az',
                           'ax_vel_az', 'ax_ot', 'scan_mode', 'scan_start', 'scan_stop', 'scan_vel',
                           'scan_scan', 'scan_nscans', 'scan_offset', 'scan_op', 'target_lon',
                           'target_lat']:
                    row[key] = 0.0 if 'target_' not in key else ''
                row['target_type'] = 'None'
                row['oph_data_valid'] = False
            
        except Exception as e:
            self.logger.warning(f"Failed to collect Oph data: {e}")
            # Fill with default/empty values
            for key in ['sc_ra', 'sc_dec', 'sc_fr', 'sc_ir', 'sc_az', 'sc_alt', 'sc_texp',
                       'sc_start_focus', 'sc_end_focus', 'sc_curr_focus', 'sc_focus_step',
                       'sc_focus_mode', 'sc_solve', 'sc_save', 'mc_curr', 'mc_sw', 'mc_lf',
                       'mc_sr', 'mc_pos', 'mc_temp', 'mc_vel', 'mc_cwr', 'mc_cww', 'mc_np',
                       'mc_pt', 'mc_it', 'mc_dt', 'ax_mode', 'ax_dest', 'ax_vel', 'ax_dest_az',
                       'ax_vel_az', 'ax_ot', 'scan_mode', 'scan_start', 'scan_stop', 'scan_vel',
                       'scan_scan', 'scan_nscans', 'scan_offset', 'scan_op', 'target_lon',
                       'target_lat']:
                row[key] = 0.0 if 'target_' not in key else ''
            row['target_type'] = 'None'
            row['oph_data_valid'] = False
        
        # Collect spectrometer timestamp data (no spectra) from GUI widget
        try:
            # Get spectrum data from the spectra widget instead of making our own calls
            if hasattr(self.main_window, 'spectra_widget') and self.main_window.spectra_widget.is_spectrometer_active():
                spec_data = self.main_window.spectra_widget.get_spectrum_data()
                if spec_data and spec_data.valid:
                    row.update({
                        'spec_timestamp': spec_data.timestamp,
                        'spec_type': spec_data.type,
                        'spec_points': spec_data.points,
                        'spec_valid': spec_data.valid
                    })
                else:
                    row.update({
                        'spec_timestamp': 0.0,
                        'spec_type': 'NONE',
                        'spec_points': 0,
                        'spec_valid': False
                    })
            else:
                row.update({
                    'spec_timestamp': 0.0,
                    'spec_type': 'NONE',
                    'spec_points': 0,
                    'spec_valid': False
                })
                
        except Exception as e:
            self.logger.warning(f"Failed to collect spectrometer data: {e}")
            row.update({
                'spec_timestamp': 0.0,
                'spec_type': 'ERROR',
                'spec_points': 0,
                'spec_valid': False
            })
        
        row['spec_data_valid'] = row.get('spec_valid', False)
        
        return row
    
    def start_logging(self) -> bool:
        """Start background logging to CSV file"""
        if self.is_logging:
            self.logger.warning("Data logging already active")
            return True
            
        try:
            # Generate log filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file_path = os.path.join(self.logs_dir, f'bcp_data_log_{timestamp}.csv')
            
            # Open CSV file for writing
            self.csv_file = open(self.log_file_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.get_csv_headers())
            
            # Write headers
            self.csv_writer.writeheader()
            self.csv_file.flush()
            
            # Start logging thread
            self.stop_event.clear()
            self.is_logging = True
            self.log_thread = threading.Thread(target=self._logging_loop, daemon=True)
            self.log_thread.start()
            
            self.logger.info(f"Data logging started - CSV file: {self.log_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start data logging: {e}")
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
            self.csv_writer = None
            self.is_logging = False
            return False
    
    def stop_logging(self):
        """Stop background logging"""
        if not self.is_logging:
            self.logger.debug("Data logging not active")
            return
            
        self.logger.info("Stopping data logging...")
        self.is_logging = False
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.log_thread and self.log_thread.is_alive():
            self.log_thread.join(timeout=2.0)
            
        # Close CSV file
        if self.csv_file:
            try:
                self.csv_file.close()
                self.logger.info(f"Data logging stopped - CSV file saved: {self.log_file_path}")
            except Exception as e:
                self.logger.error(f"Error closing CSV file: {e}")
            finally:
                self.csv_file = None
                self.csv_writer = None
                
    def resume_logging(self) -> bool:
        """Resume logging to the same file (append mode)"""
        if self.is_logging:
            self.logger.warning("Data logging already active")
            return True
            
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            self.logger.warning("No existing log file to resume - starting new log")
            return self.start_logging()
            
        try:
            # Open existing CSV file for appending
            self.csv_file = open(self.log_file_path, 'a', newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.get_csv_headers())
            
            # Start logging thread
            self.stop_event.clear()
            self.is_logging = True
            self.log_thread = threading.Thread(target=self._logging_loop, daemon=True)
            self.log_thread.start()
            
            self.logger.info(f"Data logging resumed - appending to: {self.log_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to resume data logging: {e}")
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
            self.csv_writer = None
            self.is_logging = False
            return False
    
    def _logging_loop(self):
        """Main logging loop - runs in background thread"""
        self.logger.debug("Data logging loop started")
        
        while not self.stop_event.is_set() and self.is_logging:
            try:
                loop_start_time = time.time()
                
                # Collect data from all sources via GUI widgets (NO network calls)
                data_row = self.collect_data_row()
                
                # Write to CSV file
                with self.data_lock:
                    if self.csv_writer and self.csv_file:
                        self.csv_writer.writerow(data_row)
                        self.csv_file.flush()  # Ensure data is written immediately
                
                # Calculate sleep time to maintain 1 Hz rate
                loop_duration = time.time() - loop_start_time
                sleep_time = max(0, self.log_interval - loop_duration)
                
                if sleep_time > 0:
                    self.stop_event.wait(sleep_time)
                    
            except Exception as e:
                self.logger.error(f"Error in logging loop: {e}")
                # Continue logging despite errors
                self.stop_event.wait(self.log_interval)
                
        self.logger.debug("Data logging loop stopped")
    
    def is_active(self) -> bool:
        """Check if logging is currently active"""
        return self.is_logging
    
    def get_log_file_path(self) -> Optional[str]:
        """Get the current log file path"""
        return self.log_file_path if self.is_logging else None
        
    def get_status(self) -> Dict[str, Any]:
        """Get logging status information"""
        return {
            'is_logging': self.is_logging,
            'log_file_path': self.log_file_path,
            'log_interval': self.log_interval,
            'thread_alive': self.log_thread.is_alive() if self.log_thread else False
        } 
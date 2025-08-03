"""
System Monitor Client for BVEX Ground Station
Connects to both Ophiuchus and Saggitarius flight computers for system metrics
"""

import socket
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from src.config.settings import SYSTEM_MONITOR


@dataclass
class SystemData:
    """Data structure for system monitoring metrics"""
    def __init__(self):
        # CPU metrics
        self.cpu_temp = 0.0
        self.cpu_usage = 0.0
        
        # Memory metrics
        self.mem_used = 0.0
        self.mem_total = 0.0
        self.mem_used_str = "0.0Gi"
        self.mem_total_str = "0.0Gi"
        self.mem_used_bytes = 0
        self.mem_total_bytes = 0
        
        # SSD metrics
        self.ssd_mounted = 0
        self.ssd_used = "0G"
        self.ssd_total = "0G"
        self.ssd_path = ""
        
        # Status tracking
        self.valid = False
        self.last_fetch_time = 0.0


class SystemMonitorClient:
    """UDP client for system monitoring from flight computers"""
    
    def __init__(self, system_name="ophiuchus"):
        self.system_name = system_name.lower()
        
        if self.system_name not in SYSTEM_MONITOR:
            raise ValueError(f"Unknown system: {system_name}. Must be 'ophiuchus' or 'saggitarius'")
        
        config = SYSTEM_MONITOR[self.system_name]
        self.server_ip = config['host']
        self.server_port = config['port']
        self.timeout = config['timeout']
        
        self.logger = logging.getLogger(__name__)
        
        # Current data
        self.current_data = SystemData()
        self.last_update_time = 0.0
        
        # Connection tracking
        self.connection_attempts = 0
        self.last_connection_attempt = 0.0
        self.consecutive_failures = 0
        
        # Data rate tracking
        self.bytes_received = 0
        self.last_rate_check = time.time()
        
        # Metric prefix based on system
        self.prefix = "oph_sys" if self.system_name == "ophiuchus" else "sag_sys"
        
        self.logger.info(f"System monitor client initialized for {system_name} - Server: {self.server_ip}:{self.server_port}")
    
    def get_metric(self, metric_name: str) -> str:
        """Request specific metric from system monitor server"""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Add system prefix to metric name
            full_metric_name = f"{self.prefix}_{metric_name}"
            
            # Send request
            request = full_metric_name.encode('utf-8')
            sock.sendto(request, (self.server_ip, self.server_port))
            
            # Receive response
            response, addr = sock.recvfrom(1024)
            sock.close()
            
            # Track data rate
            self.bytes_received += len(response)
            
            response_str = response.decode('utf-8').strip()
            
            # Handle system monitor disabled case
            if response_str in ["-1", "N/A"]:
                return "N/A"
            
            return response_str
        
        except socket.timeout:
            self.consecutive_failures += 1
            return "TIMEOUT"
        except Exception as e:
            self.logger.debug(f"Error getting {metric_name}: {e}")
            self.consecutive_failures += 1
            return f"ERROR: {e}"
    
    def update_data(self) -> bool:
        """Update all system monitoring data"""
        try:
            current_time = time.time()
            self.last_update_time = current_time
            self.connection_attempts += 1
            
            # Get all metrics
            metrics = {
                'cpu_temp': self.get_metric('cpu_temp'),
                'cpu_usage': self.get_metric('cpu_usage'),
                'mem_used': self.get_metric('mem_used'),
                'mem_total': self.get_metric('mem_total'),
                'mem_used_str': self.get_metric('mem_used_str'),
                'mem_total_str': self.get_metric('mem_total_str'),
                'ssd_mounted': self.get_metric('ssd_mounted'),
                'ssd_used': self.get_metric('ssd_used'),
                'ssd_total': self.get_metric('ssd_total'),
                'ssd_path': self.get_metric('ssd_path')
            }
            
            # Check if any critical metrics failed
            failed_metrics = [k for k, v in metrics.items() if v in ["TIMEOUT", "N/A"] or v.startswith("ERROR")]
            
            if len(failed_metrics) > 5:  # If more than half failed, consider it a failure
                self.logger.warning(f"Most metrics failed for {self.system_name}: {failed_metrics}")
                self.current_data.valid = False
                return False
            
            # Update data structure with successful metrics
            try:
                # CPU metrics
                if metrics['cpu_temp'] not in ["TIMEOUT", "N/A"] and not metrics['cpu_temp'].startswith("ERROR"):
                    self.current_data.cpu_temp = float(metrics['cpu_temp'])
                else:
                    self.current_data.cpu_temp = 0.0
                
                if metrics['cpu_usage'] not in ["TIMEOUT", "N/A"] and not metrics['cpu_usage'].startswith("ERROR"):
                    self.current_data.cpu_usage = float(metrics['cpu_usage'])
                else:
                    self.current_data.cpu_usage = 0.0
                
                # Memory metrics
                if metrics['mem_used'] not in ["TIMEOUT", "N/A"] and not metrics['mem_used'].startswith("ERROR"):
                    self.current_data.mem_used = float(metrics['mem_used'])
                    self.current_data.mem_used_bytes = int(float(metrics['mem_used']) * 1024 * 1024 * 1024)
                else:
                    self.current_data.mem_used = 0.0
                    self.current_data.mem_used_bytes = 0
                
                if metrics['mem_total'] not in ["TIMEOUT", "N/A"] and not metrics['mem_total'].startswith("ERROR"):
                    self.current_data.mem_total = float(metrics['mem_total'])
                    self.current_data.mem_total_bytes = int(float(metrics['mem_total']) * 1024 * 1024 * 1024)
                else:
                    self.current_data.mem_total = 0.0
                    self.current_data.mem_total_bytes = 0
                
                # Memory strings
                self.current_data.mem_used_str = metrics['mem_used_str'] if metrics['mem_used_str'] not in ["TIMEOUT", "ERROR"] else "N/A"
                self.current_data.mem_total_str = metrics['mem_total_str'] if metrics['mem_total_str'] not in ["TIMEOUT", "ERROR"] else "N/A"
                
                # SSD metrics
                if metrics['ssd_mounted'] not in ["TIMEOUT", "N/A"] and not metrics['ssd_mounted'].startswith("ERROR"):
                    self.current_data.ssd_mounted = int(metrics['ssd_mounted'])
                else:
                    self.current_data.ssd_mounted = 0
                
                self.current_data.ssd_used = metrics['ssd_used'] if metrics['ssd_used'] not in ["TIMEOUT", "ERROR"] else "N/A"
                self.current_data.ssd_total = metrics['ssd_total'] if metrics['ssd_total'] not in ["TIMEOUT", "ERROR"] else "N/A"
                self.current_data.ssd_path = metrics['ssd_path'] if metrics['ssd_path'] not in ["TIMEOUT", "ERROR"] else "N/A"
                
                self.current_data.valid = True
                self.current_data.last_fetch_time = current_time
                self.consecutive_failures = 0
                return True
                
            except (ValueError, TypeError) as e:
                self.logger.error(f"Error parsing {self.system_name} metrics: {e}")
                self.current_data.valid = False
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating {self.system_name} system data: {e}")
            self.current_data.valid = False
            return False
    
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
            
        # Consider connected if we have data from last 60 seconds
        time_since_update = time.time() - self.current_data.last_fetch_time
        return time_since_update < 60.0
    
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
        self.logger.info(f"{self.system_name.title()} system monitor client cleaned up")
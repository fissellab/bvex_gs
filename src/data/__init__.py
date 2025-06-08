# Data management and communication package 

"""
Data handling components for BVEX Ground Station
"""

import time
from collections import deque
from typing import List, Tuple


class DataRateTracker:
    """Utility class for tracking data rates over time"""
    
    def __init__(self, window_seconds: int = 30):
        """
        Initialize data rate tracker
        
        Args:
            window_seconds: Time window for rate calculation (default 30s)
        """
        self.window_seconds = window_seconds
        self.data_points = deque()  # (timestamp, bytes) pairs
        self.total_bytes = 0
        
    def add_data(self, bytes_received: int):
        """
        Add data point for rate calculation
        
        Args:
            bytes_received: Number of bytes received
        """
        current_time = time.time()
        self.data_points.append((current_time, bytes_received))
        self.total_bytes += bytes_received
        
        # Clean old data points outside window
        cutoff_time = current_time - self.window_seconds
        while self.data_points and self.data_points[0][0] < cutoff_time:
            old_timestamp, old_bytes = self.data_points.popleft()
            self.total_bytes -= old_bytes
    
    def get_rate_bps(self) -> float:
        """
        Get current data rate in bytes per second
        
        Returns:
            Data rate in bytes/second
        """
        if not self.data_points:
            return 0.0
            
        current_time = time.time()
        if len(self.data_points) < 2:
            return 0.0
            
        # Calculate rate over actual time window
        oldest_time = self.data_points[0][0]
        time_span = current_time - oldest_time
        
        if time_span <= 0:
            return 0.0
            
        return self.total_bytes / time_span
    
    def get_rate_kbps(self) -> float:
        """
        Get current data rate in kilobytes per second
        
        Returns:
            Data rate in KB/s
        """
        return self.get_rate_bps() / 1024.0
    
    def get_rate_mbps(self) -> float:
        """
        Get current data rate in megabytes per second
        
        Returns:
            Data rate in MB/s
        """
        return self.get_rate_kbps() / 1024.0
    
    def reset(self):
        """Reset all tracking data"""
        self.data_points.clear()
        self.total_bytes = 0
    
    def get_stats(self) -> dict:
        """
        Get detailed statistics
        
        Returns:
            Dictionary with rate statistics
        """
        rate_bps = self.get_rate_bps()
        return {
            'bytes_per_second': rate_bps,
            'kilobytes_per_second': rate_bps / 1024.0,
            'megabytes_per_second': rate_bps / (1024.0 * 1024.0),
            'total_bytes': sum(bytes_val for _, bytes_val in self.data_points),
            'data_points': len(self.data_points),
            'window_seconds': self.window_seconds
        } 
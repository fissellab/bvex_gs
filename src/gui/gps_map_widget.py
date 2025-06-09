"""
Compact GPS Map Widget for BVEX Ground Station
Offline Ontario map using matplotlib - no web dependencies
"""

import os
from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging
import math

# Try to import matplotlib for offline mapping
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from src.config.settings import GPS_MAP, OBSERVATORY

class GPSMapWidget(QWidget):
    """Compact GPS tracking widget - offline Ontario map display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # GPS state
        self.current_lat = None
        self.current_lon = None
        self.trail_points = []
        
        # Map settings from configuration
        self.trail_length = GPS_MAP['trail_length']
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the compact GPS interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)
        
        if MATPLOTLIB_AVAILABLE:
            # Create matplotlib-based offline map
            self.create_ontario_map()
            layout.addWidget(self.map_canvas)
        else:
            # Fallback to coordinate display
            self.coord_display = self.create_coordinate_display()
            layout.addWidget(self.coord_display)
        
        # Add distance/bearing info
        self.info_label = QLabel("Waiting for GPS data...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
    
    def create_ontario_map(self):
        """Create offline Ontario map using matplotlib"""
        # Create figure and canvas
        self.figure = Figure(figsize=(3.2, 3.0), dpi=80, facecolor='white')
        self.map_canvas = FigureCanvas(self.figure)
        self.map_canvas.setMinimumSize(250, 240)
        self.map_canvas.setMaximumSize(320, 300)
        
        # Create the plot
        self.ax = self.figure.add_subplot(111)
        self.setup_ontario_boundaries()
        self.plot_initial_positions()
        
        # Tight layout to maximize map area
        self.figure.tight_layout(pad=0.5)
    
    def setup_ontario_boundaries(self):
        """Setup local area map with clear geographic features"""
        # Focus on Kingston area with reasonable zoom
        center_lat = OBSERVATORY['latitude']  # 44.224372
        center_lon = OBSERVATORY['longitude']  # -76.498007
        
        # Set reasonable bounds - about 0.5 degree span (roughly 50km)
        span = 0.25  # degrees
        self.ax.set_xlim(center_lon - span, center_lon + span)
        self.ax.set_ylim(center_lat - span, center_lat + span)
        
        # Add geographical context
        self.ax.set_facecolor('#f0f8ff')  # Very light background
        self.ax.grid(True, alpha=0.4, linestyle='-', linewidth=0.5, color='gray')
        self.ax.set_xlabel('Longitude', fontsize=8)
        self.ax.set_ylabel('Latitude', fontsize=8)
        self.ax.tick_params(labelsize=7)
        
        # Add Lake Ontario (more accurate coordinates around Kingston)
        # Lake Ontario shoreline near Kingston
        lake_lons = [-76.8, -76.7, -76.6, -76.5, -76.4, -76.3, -76.2, -76.3, -76.4, -76.5, -76.6, -76.7, -76.8]
        lake_lats = [44.0, 43.95, 43.9, 43.85, 43.9, 43.95, 44.0, 44.05, 44.1, 44.15, 44.1, 44.05, 44.0]
        self.ax.fill(lake_lons, lake_lats, color='#87CEEB', alpha=0.6, edgecolor='blue', linewidth=1)
        
        # Add roads/highways as reference lines
        # Highway 401 (approximate path through Kingston area)
        hwy401_lons = [-76.8, -76.6, -76.4, -76.2]
        hwy401_lats = [44.18, 44.22, 44.25, 44.28]
        self.ax.plot(hwy401_lons, hwy401_lats, 'k--', linewidth=2, alpha=0.7, label='Highway 401')
        
        # Add local cities and landmarks with clear markers
        landmarks = {
            'Kingston': (-76.4951, 44.2312, 'red'),
            'Queen\'s University': (-76.4951, 44.2253, 'purple'), 
            'CFB Kingston': (-76.4700, 44.2380, 'green'),
            'Cataraqui River': (-76.4800, 44.2200, 'blue'),
        }
        
        for name, (lon, lat, color) in landmarks.items():
            # Only show landmarks that are in our current view
            if (center_lon - span <= lon <= center_lon + span and 
                center_lat - span <= lat <= center_lat + span):
                self.ax.plot(lon, lat, 'o', color=color, markersize=6, alpha=0.8)
                self.ax.annotate(name, (lon, lat), xytext=(5, 5), textcoords='offset points', 
                               fontsize=7, fontweight='bold', 
                               bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
        
        # Add compass rose in corner
        self.add_compass_rose()
        
        self.ax.set_title('BVEX GPS Tracking - Kingston Area', fontsize=10, fontweight='bold', pad=10)
    
    def add_compass_rose(self):
        """Add a simple compass rose to the map"""
        # Get current axis limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # Position compass in upper right corner
        compass_x = xlim[1] - 0.05 * (xlim[1] - xlim[0])
        compass_y = ylim[1] - 0.15 * (ylim[1] - ylim[0])
        
        # Draw simple compass
        compass_size = 0.02 * (xlim[1] - xlim[0])
        
        # North arrow
        self.ax.annotate('N', (compass_x, compass_y + compass_size), 
                        ha='center', va='bottom', fontsize=8, fontweight='bold')
        self.ax.arrow(compass_x, compass_y, 0, compass_size, 
                     head_width=compass_size*0.3, head_length=compass_size*0.2, 
                     fc='red', ec='red', alpha=0.8)
        
        # Add scale reference
        scale_x = xlim[0] + 0.05 * (xlim[1] - xlim[0])
        scale_y = ylim[0] + 0.05 * (ylim[1] - ylim[0])
        
        # 10km scale bar (approximately 0.1 degrees at this latitude)
        scale_length = 0.1
        self.ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y], 
                    'k-', linewidth=3, alpha=0.8)
        self.ax.annotate('~10 km', (scale_x + scale_length/2, scale_y), 
                        xytext=(0, -10), textcoords='offset points',
                        ha='center', fontsize=7, fontweight='bold')
    
    def plot_initial_positions(self):
        """Plot ground station marker only initially"""
        # Ground station (always visible)
        ground_lat = OBSERVATORY['latitude']
        ground_lon = OBSERVATORY['longitude']
        
        self.ground_marker = self.ax.plot(ground_lon, ground_lat, 'bs', markersize=10, 
                                         label='Ground Station', zorder=10)[0]
        
        # Add ground station annotation
        self.ax.annotate('BVEX Ground Station', 
                        (ground_lon, ground_lat), 
                        xytext=(5, 5), 
                        textcoords='offset points',
                        fontsize=8, 
                        fontweight='bold',
                        color='blue',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
        
        # Initialize balloon marker (will be updated when GPS data arrives)
        self.balloon_marker = None
        self.trail_line = None
        
        # Don't add legend - keep map clean
    
    def create_coordinate_display(self):
        """Create simple coordinate display as fallback"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setMinimumSize(250, 240)
        frame.setMaximumSize(320, 300)
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("GPS Position (Offline Mode)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("QLabel { color: #333; }")
        layout.addWidget(title)
        
        # Ground station info
        ground_label = QLabel("🏠 Ground Station:")
        ground_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        ground_label.setStyleSheet("QLabel { color: #0066cc; }")
        
        self.ground_coords = QLabel(f"{OBSERVATORY['latitude']:.5f}, {OBSERVATORY['longitude']:.5f}")
        self.ground_coords.setFont(QFont("Courier", 9))
        self.ground_coords.setStyleSheet("QLabel { color: #333; }")
        
        layout.addWidget(ground_label)
        layout.addWidget(self.ground_coords)
        
        # Balloon info
        balloon_label = QLabel("🎈 Balloon Position:")
        balloon_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        balloon_label.setStyleSheet("QLabel { color: #cc3300; }")
        
        self.balloon_coords = QLabel("Waiting for GPS data...")
        self.balloon_coords.setFont(QFont("Courier", 9))
        self.balloon_coords.setStyleSheet("QLabel { color: #333; }")
        
        layout.addWidget(balloon_label)
        layout.addWidget(self.balloon_coords)
        
        layout.addStretch()
        return frame
    
    def update_position(self, lat: float, lon: float):
        """Update balloon position on the map"""
        self.current_lat = lat
        self.current_lon = lon
        
        # Add to trail
        self.trail_points.append([lat, lon])
        if len(self.trail_points) > self.trail_length:
            self.trail_points.pop(0)
        
        if MATPLOTLIB_AVAILABLE:
            self.update_map_display()
        else:
            self.balloon_coords.setText(f"{lat:.5f}, {lon:.5f}")
        
        # Update distance/bearing info
        self.update_info_display(lat, lon)
    
    def update_map_display(self):
        """Update the matplotlib map display"""
        try:
            # Remove old balloon marker if it exists
            if self.balloon_marker:
                self.balloon_marker.remove()
            if self.trail_line:
                self.trail_line.remove()
            
            # Plot trail if we have multiple points
            if len(self.trail_points) > 1:
                trail_lons = [point[1] for point in self.trail_points]
                trail_lats = [point[0] for point in self.trail_points]
                self.trail_line = self.ax.plot(trail_lons, trail_lats, 'r-', 
                                             linewidth=2, alpha=0.7, label='Balloon trail')[0]
            
            # Plot current balloon position
            if self.current_lat and self.current_lon:
                self.balloon_marker = self.ax.plot(self.current_lon, self.current_lat, 'ro', 
                                                 markersize=8, label='Balloon', zorder=10)[0]
                
                # Add balloon annotation
                self.ax.annotate(f'Balloon\n{self.current_lat:.4f}, {self.current_lon:.4f}', 
                               (self.current_lon, self.current_lat), 
                               xytext=(5, -15), 
                               textcoords='offset points',
                               fontsize=7, 
                               color='red',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.8))
                
                # Auto-zoom to show both ground station and balloon
                self.auto_zoom()
            
            # Refresh the canvas
            self.map_canvas.draw()
            
        except Exception as e:
            self.logger.warning(f"Failed to update map display: {e}")
    
    def auto_zoom(self):
        """Automatically adjust zoom to show both ground station and balloon"""
        if not self.current_lat or not self.current_lon:
            return
            
        ground_lat = OBSERVATORY['latitude']
        ground_lon = OBSERVATORY['longitude']
        
        # Calculate distance between points
        distance_km = self.calculate_distance(ground_lat, ground_lon, self.current_lat, self.current_lon)
        
        # Set zoom based on distance between points
        if distance_km < 1:  # Very close - show detailed view
            span = 0.05  # ~5km view
        elif distance_km < 5:  # Close - show local area
            span = 0.1   # ~10km view  
        elif distance_km < 20:  # Medium distance
            span = 0.2   # ~20km view
        else:  # Far apart
            span = 0.5   # ~50km view
        
        # Center between the two points
        center_lat = (ground_lat + self.current_lat) / 2
        center_lon = (ground_lon + self.current_lon) / 2
        
        # Set bounds with padding
        self.ax.set_xlim(center_lon - span, center_lon + span)
        self.ax.set_ylim(center_lat - span, center_lat + span)
    
    def update_info_display(self, lat: float, lon: float):
        """Update distance and bearing information"""
        try:
            # Calculate distance and bearing from ground station
            ground_lat = OBSERVATORY['latitude']
            ground_lon = OBSERVATORY['longitude']
            
            distance_km = self.calculate_distance(ground_lat, ground_lon, lat, lon)
            bearing = self.calculate_bearing(ground_lat, ground_lon, lat, lon)
            
            self.info_label.setText(
                f"Distance: {distance_km:.3f} km | Bearing: {bearing:.1f}° | Trail: {len(self.trail_points)} pts"
            )
            
        except Exception as e:
            self.info_label.setText("Position calculation error")
            self.logger.warning(f"Failed to calculate position info: {e}")
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        return (bearing_deg + 360) % 360  # Normalize to 0-360
    
    def cleanup(self):
        """Clean up resources"""
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'figure'):
            plt.close(self.figure)


class MapBounds:
    """Simple bounds checking for map updates - kept for compatibility"""
    
    def __init__(self, center_lat: float, center_lon: float, zoom_level: int):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.zoom_level = zoom_level
        self.margin = 0.01 / (2 ** (zoom_level - 14))
    
    def should_update(self, lat: float, lon: float) -> bool:
        """Check if position is outside current bounds"""
        return (abs(lat - self.center_lat) > self.margin or 
                abs(lon - self.center_lon) > self.margin)
    
    def contains_point(self, lat: float, lon: float) -> bool:
        """Check if point is within bounds"""
        return not self.should_update(lat, lon) 
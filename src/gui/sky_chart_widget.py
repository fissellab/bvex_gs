"""
Sky Chart Widget for BVEX Ground Station
Displays real-time sky chart with celestial objects and telescope pointing
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from astropy.coordinates import SkyCoord, AltAz, EarthLocation, solar_system_ephemeris, get_body
from astropy.time import Time
import astropy.units as u
import datetime as dt
import logging

from src.config.settings import OBSERVATORY, CELESTIAL_OBJECTS, GUI

class SkyChartWidget(QWidget):
    """Widget displaying real-time sky chart"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_location = EarthLocation(
            lon=OBSERVATORY['longitude'] * u.degree,
            lat=OBSERVATORY['latitude'] * u.degree,
            height=OBSERVATORY['elevation'] * u.meter
        )
        
        # Control state
        self.is_active = False
        self.ani = None
        
        self.setup_ui()
        self.setup_static_display()
    
    def setup_ui(self):
        """Initialize the matplotlib figure and canvas"""
        layout = QVBoxLayout()
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("Sky Chart: OFF")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setStyleSheet("QLabel { color: red; }")
        
        # Toggle button
        self.toggle_button = QPushButton("Turn ON")
        self.toggle_button.setMinimumWidth(100)
        self.toggle_button.clicked.connect(self.toggle_state)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.toggle_button)
        
        layout.addLayout(control_layout)
        
        # Create matplotlib figure with polar projection
        self.figure = Figure(figsize=GUI['sky_chart_size'], tight_layout=True)
        self.ax = self.figure.add_subplot(111, projection='polar')
        self.canvas = FigureCanvas(self.figure)
        
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def toggle_state(self):
        """Toggle between active and inactive states"""
        if self.is_active:
            self.stop_animation()
        else:
            self.start_animation()
    
    def start_animation(self):
        """Start the sky chart animation"""
        if not self.is_active:
            self.is_active = True
            self.status_label.setText("Sky Chart: ON")
            self.status_label.setStyleSheet("QLabel { color: green; }")
            self.toggle_button.setText("Turn OFF")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            
            # Start animation
            self.setup_animation()
    
    def stop_animation(self):
        """Stop the sky chart animation and show static display"""
        if self.is_active:
            self.is_active = False
            self.status_label.setText("Sky Chart: OFF")
            self.status_label.setStyleSheet("QLabel { color: red; }")
            self.toggle_button.setText("Turn ON")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            
            # Stop animation
            if self.ani is not None:
                try:
                    self.ani.event_source.stop()
                except Exception:
                    pass  # Animation might already be stopped
                self.ani = None
            
            # Show static display
            self.setup_static_display()
    
    def setup_static_display(self):
        """Show static 'waiting for user input' display"""
        self.ax.clear()
        self.ax.set_rlim(90, 0)
        self.ax.set_theta_zero_location("N")
        self.ax.grid(True, alpha=0.3, linewidth=0.5)
        self.ax.set_title("Sky Chart - Waiting for User Input", fontsize=14, pad=20, color='gray')
        
        # Add centered text
        self.ax.text(0, 45, 'Click "Turn ON" to start\nsky chart updates', 
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=16, color='gray', weight='bold')
        
        self.canvas.draw()
    
    def setup_animation(self):
        """Setup matplotlib FuncAnimation - EXACT approach from original bvex_pointing.py"""
        if self.is_active:
            # Stop any existing animation first
            if self.ani is not None:
                self.ani.event_source.stop()
                self.ani = None
            
            # Use FuncAnimation exactly like the original - this handles polar plot clearing properly
            self.ani = animation.FuncAnimation(
                self.figure, 
                self.update_chart, 
                interval=GUI['update_interval'], 
                cache_frame_data=False,
                repeat=True,
                blit=False
            )
            
            # Force canvas to draw to ensure animation is properly initialized
            self.canvas.draw_idle()
    
    def update_location(self, latitude: float, longitude: float, elevation: float = None):
        """Update observer location (e.g., from GPS data)"""
        if elevation is None:
            elevation = OBSERVATORY['elevation']
            
        self.current_location = EarthLocation(
            lon=longitude * u.degree,
            lat=latitude * u.degree,
            height=elevation * u.meter
        )
    
    def update_chart(self, frame):
        """Update the sky chart with current celestial positions - EXACT logic from original"""
        if not self.is_active:
            return
            
        # EXACT clearing approach from original bvex_pointing.py
        self.ax.clear()
        
        # Current time and observing frame - use exact same format as original
        t_utc = Time(dt.datetime.now(dt.timezone.utc))
        tel_frame = AltAz(location=self.current_location, obstime=t_utc)
        
        # Draw coordinate grid
        self._draw_coordinate_grid(tel_frame)
        
        # Draw celestial objects
        self._draw_solar_system_objects(tel_frame)
        
        # Draw observation targets
        self._draw_targets(tel_frame)
        
        # Configure plot appearance
        self._configure_plot(t_utc)
    
    def set_gps_data(self, gps_data):
        """Set GPS data for heading display"""
        self.current_gps_data = gps_data
    
    def is_sky_chart_active(self) -> bool:
        """Return whether sky chart is currently active"""
        return self.is_active
    
    def _draw_coordinate_grid(self, tel_frame):
        """Draw RA/Dec coordinate grid - EXACT logic from original bvex_pointing.py"""
        ra_lines = np.linspace(0, 345, num=24)
        dec_lines = np.linspace(-80, 80, num=9)
        lat_line_ra = np.linspace(0, 360, num=1000)
        lon_line_dec = np.linspace(-90, 90, num=1000)
        const_line = np.ones(1000)
        
        # RA lines (hour circles) - Following bvex_pointing.py logic safely
        drawn_ra_labels_az = []
        for r in ra_lines:
            line = SkyCoord(ra=r * const_line * u.degree, dec=lon_line_dec * u.degree)
            line_AltAz = line.transform_to(tel_frame)
            vis = np.where(line_AltAz.alt.deg > 0)
            alt = line_AltAz.alt.deg[vis]
            az = line_AltAz.az.deg[vis]
            self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.3, linewidth=0.5)

            # Add RA labels in a ring just inside the plot boundary
            if len(alt) > 0:
                # Find where the line intersects a low altitude (e.g., 5 degrees)
                # This helps to place the labels on the outside edge of the plot
                try:
                    # Find the point on the line closest to the target altitude for labeling
                    label_alt_target = 5  # degrees
                    label_idx = np.argmin(np.abs(alt - label_alt_target))
                    
                    # Ensure it's a reasonable point to label
                    if np.abs(alt[label_idx] - label_alt_target) < 10:
                        az_deg = az[label_idx]
                        
                        # Check for overlap with other labels
                        is_too_close = any(
                            min(abs(az_deg - old_az), 360 - abs(az_deg - old_az)) < 20
                            for old_az in drawn_ra_labels_az
                        )
                        
                        if not is_too_close:
                            self.ax.annotate(text=f"{int(r/15)}h",
                                           xy=(np.deg2rad(az_deg), alt[label_idx]),
                                           color="blue", size=10, weight='normal',
                                           ha='center')
                            drawn_ra_labels_az.append(az_deg)
                except (ValueError, IndexError):
                    pass # Skip if no suitable point found

        # Dec lines (declination circles) - Cleaned up styling
        for d in dec_lines:
            line = SkyCoord(ra=lat_line_ra * u.degree, dec=d * const_line * u.degree)
            line_AltAz = line.transform_to(tel_frame)
            vis = np.where(line_AltAz.alt.deg > 0)
            alt = line_AltAz.alt.deg[vis]
            az = line_AltAz.az.deg[vis]
            self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.2, linewidth=0.5)
            # Keep the original buggy condition exactly as it was
            if len(alt) > 11:
                try:
                    # Place label at the middle of the visible arc
                    label_idx = len(alt) // 2
                    self.ax.annotate(text=f"{int(d)}$^\\circ$",
                                   xy=(az[label_idx] * np.pi / 180, alt[label_idx]),
                                   color="blue", size=9, alpha=0.8, weight='normal')
                except IndexError:
                    pass  # Skip annotation if not enough points
    
    def _draw_solar_system_objects(self, tel_frame):
        """Draw solar system objects - EXACT logic from original bvex_pointing.py"""
        sso = ['sun','moon','mercury','venus', 'mars','jupiter','saturn', 'uranus','neptune']
        
        for obj in sso:
            try:
                with solar_system_ephemeris.set('builtin'):
                    body = get_body(obj, tel_frame.obstime, self.current_location)
                    body_AltAz = body.transform_to(tel_frame)
                    body_alt = body_AltAz.alt.deg
                    body_az = body_AltAz.az.deg
                    
                    if body_alt > 0:
                        if(obj == 'sun'):
                            self.ax.plot(body_az * np.pi / 180, body_alt, 'yo', markersize=10, label='Sun')
                            self.ax.annotate('Sun', xy=((body_az + 1) * np.pi / 180, body_alt + 1), 
                                           size=11, color='orange', weight='bold')
                        elif(obj == 'moon'):
                            self.ax.plot(body_AltAz.az.deg * np.pi / 180, body_AltAz.alt.deg, 'ko', markersize=7)
                            self.ax.annotate('Moon', xy=((body_az + 1) * np.pi / 180, body_alt + 1), 
                                           size=11, color='gray', weight='bold')
                        else:
                            self.ax.plot(body_AltAz.az.deg * np.pi / 180, body_AltAz.alt.deg, 'k.', markersize=5)
                            self.ax.annotate(obj.capitalize(), xy=((body_az + 1) * np.pi / 180, body_alt + 1), 
                                           size=10, color='black', alpha=0.9)
            except Exception as e:
                logging.warning(f"Could not calculate position for '{obj}': {e}")
                continue
    
    def _draw_targets(self, tel_frame):
        """Draw observation targets - EXACT logic from original bvex_pointing.py"""
        # W49N target - EXACT coordinates and logic from original
        W49N = SkyCoord(ra='19h11m28.37s', dec='09d06m02.2s')
        W49N_AltAz = W49N.transform_to(tel_frame)
        
        if(W49N_AltAz.alt.deg > 0):
            self.ax.plot(W49N_AltAz.az.deg * np.pi / 180, W49N_AltAz.alt.deg, 'gv', markersize=9)
            self.ax.annotate('W49N', xy=((W49N_AltAz.az.deg + 1) * np.pi / 180, W49N_AltAz.alt.deg + 1), 
                           size=11, color='green', weight='bold')
    
    def _configure_plot(self, time_utc):
        """Configure plot appearance - EXACT settings from original bvex_pointing.py"""
        self.ax.set_rlim(90, 0)  # EXACT from original
        self.ax.set_rticks([80, 60, 40, 20])  # EXACT from original
        self.ax.grid(True, alpha=0.3, linewidth=0.5)  # Cleaner grid
        self.ax.set_theta_zero_location("N")  # EXACT from original
        self.ax.tick_params(labelsize=10)  # Smaller, cleaner tick labels
        time_str = str(time_utc).split('.')[0]
        self.ax.set_title(f"Current Sky UTC: {time_str}", fontsize=14, pad=20)
 
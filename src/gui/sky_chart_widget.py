"""
Sky Chart Widget for BVEX Ground Station
Displays real-time sky chart with celestial objects and telescope pointing
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer

from astropy.coordinates import SkyCoord, AltAz, EarthLocation, solar_system_ephemeris, get_body
from astropy.time import Time
import astropy.units as u
import datetime as dt

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
        
        self.setup_ui()
        self.setup_update_timer()
    
    def setup_ui(self):
        """Initialize the matplotlib figure and canvas"""
        layout = QVBoxLayout()
        
        # Create matplotlib figure with polar projection
        self.figure = Figure(figsize=GUI['sky_chart_size'], tight_layout=True)
        self.ax = self.figure.add_subplot(111, projection='polar')
        self.canvas = FigureCanvas(self.figure)
        
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Initial plot
        self.update_chart()
    
    def setup_update_timer(self):
        """Setup timer for regular chart updates"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(GUI['update_interval'])  # Update every second
    
    def update_location(self, latitude: float, longitude: float, elevation: float = None):
        """Update observer location (e.g., from GPS data)"""
        if elevation is None:
            elevation = OBSERVATORY['elevation']
            
        self.current_location = EarthLocation(
            lon=longitude * u.degree,
            lat=latitude * u.degree,
            height=elevation * u.meter
        )
    
    def update_chart(self):
        """Update the sky chart with current celestial positions"""
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
        
        # Draw GPS heading indicator (if GPS data available)
        self._draw_gps_heading()
        
        # Configure plot appearance
        self._configure_plot(t_utc)
        
        # Refresh canvas
        self.canvas.draw()
    
    def set_gps_data(self, gps_data):
        """Set GPS data for heading display"""
        self.current_gps_data = gps_data
    
    def _draw_gps_heading(self):
        """GPS heading display removed - no arrow overlay"""
        pass
    
    def _draw_coordinate_grid(self, tel_frame):
        """Draw RA/Dec coordinate grid - EXACT logic from original bvex_pointing.py"""
        ra_lines = np.linspace(0, 345, num=24)
        dec_lines = np.linspace(-80, 80, num=9)
        lat_line_ra = np.linspace(0, 360, num=1000)
        lon_line_dec = np.linspace(-90, 90, num=1000)
        const_line = np.ones(1000)
        
        # RA lines (hour circles) - EXACT logic from original
        for r in ra_lines:
            line = SkyCoord(ra=r * const_line * u.degree, dec=lon_line_dec * u.degree)
            line_AltAz = line.transform_to(tel_frame)
            vis = np.where(line_AltAz.alt.deg > 0)
            alt = line_AltAz.alt.deg[vis]
            az = line_AltAz.az.deg[vis]
            self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.2, linewidth=0.5)
            # Smaller, more subtle hour labels
            self.ax.annotate(text=str(int(r / 15)) + 'h', 
                           xy=(az[30] * np.pi / 180, alt[30]), 
                           color="blue", size=8, alpha=0.7)
        
        # Dec lines (declination circles) - EXACT logic from original with bug fix
        for d in dec_lines:
            line = SkyCoord(ra=lat_line_ra * u.degree, dec=d * const_line * u.degree)
            line_AltAz = line.transform_to(tel_frame)
            vis = np.where(line_AltAz.alt.deg > 0)
            alt = line_AltAz.alt.deg[vis]
            az = line_AltAz.az.deg[vis]
            self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.2, linewidth=0.5)
            # Fixed the original bug: len(alt>11) should be len(alt) > 11
            if len(alt) > 11:
                self.ax.annotate(text=str(int(d)) + '°',
                               xy=(az[10] * np.pi / 180, alt[10]),
                               color="blue", size=8, alpha=0.7)
    
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
                        if obj == 'sun':
                            self.ax.plot(body_az * np.pi / 180, body_alt, 'yo', markersize=6)
                            # Smaller, cleaner annotation positioning from original - using +1 offset
                            self.ax.annotate('Sun', xy=((body_az + 1) * np.pi / 180, body_alt + 1), 
                                           size=9, color='orange', weight='bold')
                        elif obj == 'moon':
                            self.ax.plot(body_AltAz.az.deg * np.pi / 180, body_AltAz.alt.deg, 'ko', markersize=5)
                            # Smaller, cleaner annotation positioning from original - using +1 offset
                            self.ax.annotate('Moon', xy=((body_az + 1) * np.pi / 180, body_alt + 1), 
                                           size=9, color='gray', weight='bold')
                        else:
                            self.ax.plot(body_AltAz.az.deg * np.pi / 180, body_AltAz.alt.deg, 'k.', markersize=3)
                            # Smaller, cleaner annotation positioning from original - using +1 offset
                            self.ax.annotate(obj, xy=((body_az + 1) * np.pi / 180, body_alt + 1), 
                                           size=8, color='black', alpha=0.8)
            except Exception:
                continue
    
    def _draw_targets(self, tel_frame):
        """Draw observation targets - EXACT logic from original bvex_pointing.py"""
        # W49N target - EXACT coordinates and logic from original
        W49N = SkyCoord(ra='19h11m28.37s', dec='09d06m02.2s')
        W49N_AltAz = W49N.transform_to(tel_frame)
        
        if W49N_AltAz.alt.deg > 0:
            self.ax.plot(W49N_AltAz.az.deg * np.pi / 180, W49N_AltAz.alt.deg, 'gv', markersize=6)
            # Smaller, cleaner annotation positioning from original - using +1 offset
            self.ax.annotate('W49N', xy=((W49N_AltAz.az.deg + 1) * np.pi / 180, W49N_AltAz.alt.deg + 1), 
                           size=9, color='green', weight='bold')
    
    def _configure_plot(self, time_utc):
        """Configure plot appearance - EXACT settings from original bvex_pointing.py"""
        self.ax.set_rlim(90, 0)  # EXACT from original
        self.ax.set_rticks([80, 60, 40, 20])  # EXACT from original
        self.ax.grid(True, alpha=0.3, linewidth=0.5)  # More subtle grid
        self.ax.set_theta_zero_location("N")  # EXACT from original
        
        # Much smaller tick label size for cleaner appearance
        self.ax.tick_params(labelsize=9)
        
        # Smaller, cleaner title format from original
        self.ax.set_title("Current Sky UTC: " + str(time_utc), fontsize=10, pad=15)
 
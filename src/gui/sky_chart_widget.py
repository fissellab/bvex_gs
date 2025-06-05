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
        
        # Current time and observing frame (compatible with Python 3.10)
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
        """Draw RA/Dec coordinate grid with clean styling but correct logic"""
        ra_lines = np.linspace(0, 345, num=24)
        dec_lines = np.linspace(-80, 80, num=9)
        lat_line_ra = np.linspace(0, 360, num=1000)
        lon_line_dec = np.linspace(-90, 90, num=1000)
        const_line = np.ones(1000)
        
        # RA lines (hour circles) - correct logic, clean styling
        for r in ra_lines:
            line = SkyCoord(ra=r * const_line * u.degree, dec=lon_line_dec * u.degree)
            line_altaz = line.transform_to(tel_frame)
            vis = np.where(line_altaz.alt.deg > 0)
            
            if len(vis[0]) > 0:
                alt = line_altaz.alt.deg[vis]
                az = line_altaz.az.deg[vis]
                self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.3, linewidth=0.5)
                
                # Clean hour labels
                if len(alt) > 30:
                    hour_label = str(int(r / 15)) + 'h'
                    self.ax.annotate(hour_label, 
                                   xy=(az[30] * np.pi / 180, alt[30]),
                                   color="blue", size=8, alpha=0.7)
        
        # Dec lines (declination circles) - correct logic, clean styling
        for d in dec_lines:
            line = SkyCoord(ra=lat_line_ra * u.degree, dec=d * const_line * u.degree)
            line_altaz = line.transform_to(tel_frame)
            vis = np.where(line_altaz.alt.deg > 0)
            
            if len(vis[0]) > 0:
                alt = line_altaz.alt.deg[vis]
                az = line_altaz.az.deg[vis]
                self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.3, linewidth=0.5)
                
                # Clean declination labels
                if len(alt) > 10:
                    dec_label = str(int(d)) + '°'
                    self.ax.annotate(dec_label,
                                   xy=(az[10] * np.pi / 180, alt[10]),
                                   color="blue", size=8, alpha=0.7)
    
    def _draw_solar_system_objects(self, tel_frame):
        """Draw solar system objects with clean styling"""
        solar_objects = ['sun','moon','mercury','venus', 'mars','jupiter','saturn', 'uranus','neptune']
        
        for obj in solar_objects:
            try:
                with solar_system_ephemeris.set('builtin'):
                    body = get_body(obj, tel_frame.obstime, self.current_location)
                    body_altaz = body.transform_to(tel_frame)
                    
                    if body_altaz.alt.deg > 0:
                        az_rad = body_altaz.az.deg * np.pi / 180
                        alt_deg = body_altaz.alt.deg
                        
                        if obj == 'sun':
                            self.ax.plot(az_rad, alt_deg, 'yo', markersize=8)
                            self.ax.annotate('Sun', xy=(az_rad, alt_deg), 
                                           xytext=(5, 5), textcoords='offset points',
                                           fontsize=10, color='orange', weight='bold')
                        elif obj == 'moon':
                            self.ax.plot(az_rad, alt_deg, 'ko', markersize=6)
                            self.ax.annotate('Moon', xy=(az_rad, alt_deg),
                                           xytext=(5, 5), textcoords='offset points',
                                           fontsize=10, color='gray', weight='bold')
                        else:
                            self.ax.plot(az_rad, alt_deg, 'k.', markersize=4)
                            self.ax.annotate(obj, xy=(az_rad, alt_deg),
                                           xytext=(3, 3), textcoords='offset points',
                                           fontsize=8, color='black', alpha=0.8)
            except Exception:
                continue
    
    def _draw_targets(self, tel_frame):
        """Draw observation targets with clean styling"""
        # W49N target
        W49N = SkyCoord(ra='19h11m28.37s', dec='09d06m02.2s')
        W49N_altaz = W49N.transform_to(tel_frame)
        
        if W49N_altaz.alt.deg > 0:
            az_rad = W49N_altaz.az.deg * np.pi / 180
            alt_deg = W49N_altaz.alt.deg
            
            self.ax.plot(az_rad, alt_deg, 'gv', markersize=8)
            self.ax.annotate('W49N', xy=(az_rad, alt_deg),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=10, color='green', weight='bold')
    
    def _configure_plot(self, time_utc):
        """Configure plot appearance and labels"""
        self.ax.set_rlim(90, 0)  # Altitude from horizon (0°) to zenith (90°)
        self.ax.set_rticks([80, 60, 40, 20])
        self.ax.grid(True, alpha=0.3)
        self.ax.set_theta_zero_location("N")  # North at top
        
        # Clean, smaller tick labels
        self.ax.tick_params(labelsize=10)
        
        # Clean title with current time
        title = f"Current Sky UTC: {time_utc.iso[:19]}"
        self.ax.set_title(title, fontsize=12, pad=20)
 
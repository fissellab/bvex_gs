"""
Sky Chart Widget for BVEX Ground Station
Displays real-time sky chart with celestial objects and telescope pointing
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from astropy.coordinates import SkyCoord, AltAz, EarthLocation, solar_system_ephemeris, get_body
from astropy.time import Time
import astropy.units as u
import datetime as dt
import logging
from scipy.interpolate import interp1d

from src.config.settings import OBSERVATORY, CELESTIAL_OBJECTS, GUI
from src.data.Oph_client import OphClient, OphData
from src.data.gps_client import GPSClient, GPSData

class SkyChartWidget(QWidget):
    """Widget displaying real-time sky chart"""
    
    def __init__(self, parent=None, oph_client=None):
        super().__init__(parent)
        self.current_location = EarthLocation(
            lon=OBSERVATORY['longitude'] * u.degree,
            lat=OBSERVATORY['latitude'] * u.degree,
            height=OBSERVATORY['elevation'] * u.meter
        )
        
        # Control state
        self.is_active = False
        self.ani = None
        
        # Use shared Ophiuchus client for motor and star camera data if provided
        self.oph_client = oph_client if oph_client else OphClient()
        self.owns_oph_client = oph_client is None  # Track if we own the client
        
        # Star camera data for crosshair
        self.star_camera_data = OphData()
        self.gps_data = GPSData()
        
        # Coordinate system toggle for crosshair
        self.use_az_alt_coordinates = False  # False = RA/DEC, True = Az/Alt
        
        # Last known crosshair positions for persistence during data outages
        self.last_crosshair_az_rad = None
        self.last_crosshair_alt_deg = None
        self.last_crosshair_mode = None  # Track which mode the last position was from
        
        self.setup_ui()
        self.setup_static_display()
    
    def setup_ui(self):
        """Initialize the matplotlib figure and canvas"""
        # Use QGridLayout: 2 rows, 1 column (Control panel | Canvas)
        layout = QGridLayout()
        
        # Control panel - Row 0
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
        
        # Coordinate system toggle for crosshair - make it more prominent
        self.coord_checkbox = QCheckBox("Use Az/Alt for Crosshair")
        self.coord_checkbox.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.coord_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333333;
                spacing: 8px;
                background-color: #f0f0f0;
                padding: 4px 8px;
                border-radius: 4px;
                border: 1px solid #cccccc;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #666666;
                background-color: white;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #007ACC;
                background-color: #007ACC;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked:pressed {
                background-color: #005A9E;
            }
        """)
        self.coord_checkbox.setToolTip("Toggle between RA/DEC and Azimuth/Altitude coordinates for star camera crosshair")
        self.coord_checkbox.stateChanged.connect(self.toggle_coordinate_system)
        control_layout.addWidget(self.coord_checkbox)
        
        control_layout.addStretch()
        control_layout.addWidget(self.toggle_button)
        
        # Create widget container for control layout and add to grid
        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        layout.addWidget(control_widget, 0, 0)
        
        # Create matplotlib figure with polar projection - Row 1
        self.figure = Figure(figsize=GUI['sky_chart_size'], tight_layout=True)
        self.ax = self.figure.add_subplot(111, projection='polar')
        self.canvas = FigureCanvas(self.figure)
        
        layout.addWidget(self.canvas, 1, 0)
        
        # Set row stretch to make canvas expand
        layout.setRowStretch(1, 1)
        
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
        self.ax.set_rticks([80, 60, 40, 20])
        self.ax.set_theta_zero_location("N")
        self.ax.grid(True, alpha=1.0, linewidth=0.5)
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
    
    def update_location(self):
        """Update observer location (e.g., from GPS data)"""
        if self.gps_data.valid:
            self.current_location = EarthLocation(
                lon=self.gps_data.lat * u.degree,
                lat=self.gps_data.lon * u.degree,
                height=self.gps_data.alt * u.meter
            )
        else:
            self.current_location = EarthLocation(
                lon=OBSERVATORY['longitude'] * u.degree,
                lat=OBSERVATORY['latitude'] * u.degree,
                height=OBSERVATORY['elevation'] * u.meter
            )
    
    def update_chart(self, frame):
        """Update the sky chart with current celestial positions - EXACT logic from original"""
        if not self.is_active:
            return
            
        # EXACT clearing approach from original bvex_pointing.py
        self.ax.clear()
        
        #Update location
        self.update_location()
        
        # Current time and observing frame - use exact same format as original
        t_utc = Time(dt.datetime.now(dt.timezone.utc))
        tel_frame = AltAz(location=self.current_location, obstime=t_utc)
        
        # Draw coordinate grid
        self._draw_coordinate_grid(tel_frame)
        
        # Draw celestial objects
        self._draw_solar_system_objects(tel_frame)
        
        #Draw miky way
        self._draw_milky_way(tel_frame)
        
        # Draw observation targets
        self._draw_targets(tel_frame)
        
        # Draw star camera crosshair
        self._draw_star_camera_crosshair(tel_frame)
        
        # Draw elevation mount pointing crosshair
        self._draw_el_mount_crosshair()
        
        # Configure plot appearance
        self._configure_plot(t_utc)
    
    def set_gps_data(self, gps_data):
        """Set GPS data for heading display"""
        self.current_gps_data = gps_data
    
    def set_star_camera_data(self, oph_data: OphData):
        """Set star camera data for crosshair display"""
        self.star_camera_data = oph_data
    
    def toggle_coordinate_system(self, state):
        """Toggle between RA/DEC and Az/Alt coordinate systems for crosshair"""
        self.use_az_alt_coordinates = state == Qt.CheckState.Checked.value
    
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
            self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.5, linewidth=0.5)

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
            if(d<self.current_location.lat.degree):
                sort_idx = np.argsort(az)
                alt = alt[sort_idx]
                az = az[sort_idx]
            self.ax.plot(az * np.pi / 180, alt, 'b-', alpha=0.5, linewidth=0.5)
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
        OrionKL = SkyCoord(ra='05h35m14.16s', dec='-05d22m21.5s')
        OrionKL_AltAz = OrionKL.transform_to(tel_frame)
        q_3C273 = SkyCoord(ra='12h29m6.7s', dec='02d03m09s')
        q_3C273_AltAz = q_3C273.transform_to(tel_frame)
        q_3C279 = SkyCoord(ra='12h56m11.1s', dec='-05d47m22s')
        q_3C279_AltAz = q_3C279.transform_to(tel_frame)
        q_3C4543 = SkyCoord(ra='22h53m57.7s', dec='16d08m53.6s')
        q_3C4543_AltAz = q_3C4543.transform_to(tel_frame)
        q_4C1169 = SkyCoord(ra='22h32m36.4s', dec='11d43m50.9s')
        q_4C1169_AltAz = q_4C1169.transform_to(tel_frame)
        q_3C84 = SkyCoord(ra='03h19m48.2s', dec='41d30m42.1s')
        q_3C84_AltAz = q_3C84.transform_to(tel_frame)
        
        if(W49N_AltAz.alt.deg > 0):
            self.ax.plot(W49N_AltAz.az.deg * np.pi / 180, W49N_AltAz.alt.deg, 'gv', markersize=9)
            self.ax.annotate('W49N', xy=((W49N_AltAz.az.deg + 1) * np.pi / 180, W49N_AltAz.alt.deg + 1), 
                           size=11, color='green', weight='bold')
        if(OrionKL_AltAz.alt.deg > 0):
            self.ax.plot(OrionKL_AltAz.az.deg * np.pi / 180, OrionKL_AltAz.alt.deg, 'gv', markersize=9)
            self.ax.annotate('Orion KL', xy=((OrionKL_AltAz.az.deg + 1) * np.pi / 180, OrionKL_AltAz.alt.deg + 1), 
                           size=11, color='green', weight='bold')
                           
        if(q_3C273_AltAz.alt.deg > 0):
            self.ax.plot(q_3C273_AltAz.az.deg * np.pi / 180, q_3C273_AltAz.alt.deg, 'rd', markersize=9)
            self.ax.annotate('3C 273', xy=((q_3C273_AltAz.az.deg + 5) * np.pi / 180, q_3C273_AltAz.alt.deg + 5), 
                           size=11, color='red', weight='bold')
        if(q_3C279_AltAz.alt.deg > 0):
            self.ax.plot(q_3C279_AltAz.az.deg * np.pi / 180, q_3C279_AltAz.alt.deg, 'rd', markersize=9)
            self.ax.annotate('3C 279', xy=((q_3C279_AltAz.az.deg + 5) * np.pi / 180, q_3C279_AltAz.alt.deg - 5), 
                           size=11, color='red', weight='bold')
        if(q_3C4543_AltAz.alt.deg > 0):
            self.ax.plot(q_3C4543_AltAz.az.deg * np.pi / 180, q_3C4543_AltAz.alt.deg, 'rd', markersize=9)
            self.ax.annotate('3C 454.3', xy=((q_3C4543_AltAz.az.deg + 5) * np.pi / 180, q_3C4543_AltAz.alt.deg + 5), 
                           size=11, color='red', weight='bold')
        if(q_4C1169_AltAz.alt.deg > 0):
            self.ax.plot(q_4C1169_AltAz.az.deg * np.pi / 180, q_4C1169_AltAz.alt.deg, 'rd', markersize=9)
            self.ax.annotate('4C 11.69', xy=((q_4C1169_AltAz.az.deg + 5) * np.pi / 180, q_4C1169_AltAz.alt.deg + 5), 
                           size=11, color='red', weight='bold')
        if(q_3C84_AltAz.alt.deg > 0):
            self.ax.plot(q_3C84_AltAz.az.deg * np.pi / 180, q_3C84_AltAz.alt.deg, 'rd', markersize=9)
            self.ax.annotate('3C 84', xy=((q_3C84_AltAz.az.deg + 5) * np.pi / 180, q_3C84_AltAz.alt.deg + 5), 
                           size=11, color='red', weight='bold')
    def _draw_milky_way(self, tel_frame):
        gal_lats = np.linspace(-10,10,num=30)
        for bs in gal_lats:
            mw = SkyCoord(l=np.linspace(0,360,num=1000)*u.degree,b = bs*u.degree, frame='galactic')
            mw_AltAz = mw.transform_to(tel_frame)
            vis = np.where(mw_AltAz.alt.deg>0)
            if len(vis[0])>2:
                self.ax.plot(mw_AltAz.az.deg * np.pi/180,mw_AltAz.alt.deg,'k-',alpha=0.2)
        
        
    def _draw_star_camera_crosshair(self, tel_frame):
        """Draw crosshair showing star camera pointing direction with persistence during data outages"""
        # Try to update crosshair position with new valid data
        new_az_rad = None
        new_alt_deg = None
        current_mode = "az_alt" if self.use_az_alt_coordinates else "ra_dec"
        
        try:
            if self.use_az_alt_coordinates:
                # Use Az from GPS heading and Alt from motor position
                # Get current motor and GPS data
                gps_valid = getattr(self.gps_data, 'valid', False)
                gps_head = getattr(self.gps_data, 'head', 0.0)
                
                # Get motor position from shared OphClient (actual motor elevation)
                motor_data = self.oph_client.get_data() if self.oph_client else OphData()
                motor_valid = motor_data.valid if motor_data else False
                motor_pos = getattr(motor_data, 'mc_pos', 0.0) if motor_data else 0.0
                
                print(f"DEBUG Az/Alt: GPS valid={gps_valid}, head={gps_head}°, Motor valid={motor_valid}, pos={motor_pos}°")
                
                # Require GPS data for azimuth, motor position for elevation
                if gps_valid and hasattr(self.gps_data, 'head') and motor_valid:
                    gps_az = self.gps_data.head  # degrees - true heading from GPS
                    motor_alt = motor_pos  # degrees - actual motor elevation position
                    
                    # Use GPS heading for azimuth and motor position for elevation
                    new_az_rad = gps_az * np.pi / 180
                    new_alt_deg = motor_alt
                    print(f"DEBUG: Drawing Az/Alt crosshair at az={gps_az}°, alt={motor_alt}°")
                
            else:
                # Use RA/DEC coordinates (original implementation)
                if self.star_camera_data.valid:
                    sc_ra = self.star_camera_data.sc_ra  # degrees
                    sc_dec = self.star_camera_data.sc_dec  # degrees
                    
                    # Note: We plot even if RA/DEC are zero (no solution) as requested
                        
                    # Create sky coordinate from star camera RA/DEC
                    star_camera_coord = SkyCoord(ra=sc_ra * u.degree, dec=sc_dec * u.degree)
                    
                    # Transform to Alt/Az
                    star_camera_altaz = star_camera_coord.transform_to(tel_frame)
                    
                    new_az_rad = star_camera_altaz.az.deg * np.pi / 180
                    new_alt_deg = star_camera_altaz.alt.deg
        
        except Exception as e:
            # Silently skip if coordinate transformation fails
            pass
        
        # Update stored position if we have new valid data
        if new_az_rad is not None and new_alt_deg is not None and new_alt_deg > 0:
            self.last_crosshair_az_rad = new_az_rad
            self.last_crosshair_alt_deg = new_alt_deg
            self.last_crosshair_mode = current_mode
        
        # Draw crosshair using last known position (if available and matches current mode)
        if (self.last_crosshair_az_rad is not None and 
            self.last_crosshair_alt_deg is not None and 
            self.last_crosshair_mode == current_mode and
            self.last_crosshair_alt_deg > 0):
            
            # Draw crosshair - simple cross design
            alpha = 0.9 if (new_az_rad is not None and new_alt_deg is not None) else 0.6  # Dimmer if using old data
            self.ax.plot(self.last_crosshair_az_rad, self.last_crosshair_alt_deg, 'r+', 
                        markersize=20, alpha=alpha)
            
    def _draw_el_mount_crosshair(self):
        """Draw crosshair showing elevation mount pointing direction"""
        if (self.star_camera_data.valid and self.gps_data.valid):
            
            try:
                # Use motor poisiton for alt and gps heading for az
               gps_az = self.gps_data.head  # degrees
               mc_alt = self.star_camera_data.mc_pos  # degrees (altitude/elevation)
                

               az_rad = gps_az * np.pi / 180
                
            
               if mc_alt > 0:
                   # Draw crosshair - simple cross design
                   self.ax.plot(az_rad, mc_alt, 'b+', markersize=20, alpha=0.9)
            
                               
            except Exception as e:
                # Silently skip if coordinate transformation fails
                pass
        else:
            return

    def _configure_plot(self, time_utc):
        """Configure plot appearance - EXACT settings from original bvex_pointing.py"""
        self.ax.set_rlim(90, 0)  # EXACT from original
        self.ax.set_rticks([80, 60, 40, 20])  # EXACT from original
        self.ax.grid(True, alpha=1.0, linewidth=0.5)  # Cleaner grid
        self.ax.set_theta_zero_location("N")  # EXACT from original
        self.ax.tick_params(labelsize=10)  # Smaller, cleaner tick labels
        time_str = str(time_utc).split('.')[0]
        self.ax.set_title(f"Current Sky UTC: {time_str}", fontsize=14, pad=20)
 

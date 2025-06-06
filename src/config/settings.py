"""
BVEX Ground Station Configuration Settings
"""

# GPS Server Configuration
GPS_SERVER = {
    'host': '100.70.234.8',
    'port': 8080,  # You'll need to verify this port
    'request_message': 'GET_GPS',
    'timeout': 5.0,
    'update_interval': 0.05  # 50ms between requests
}

# BCP Spectrometer Configuration
BCP_SPECTROMETER = {
    'host': '100.70.234.8',  # Saggitarius system IP
    'port': 8081,
    'timeout': 5.0,
    'update_interval': 1.0   # 1 second = 1 Hz updates
}

# GPS Data Processing
GPS_PROCESSING = {
    'heading_offset': 90.0,  # degrees - constant offset to add to GPS heading
    'coordinate_offset_lat': 0.0,  # degrees - offset for latitude if needed
    'coordinate_offset_lon': 0.0   # degrees - offset for longitude if needed
}

# Default Observatory Location (Kingston, ON area)
OBSERVATORY = {
    'latitude': 44.224372,   # degrees
    'longitude': -76.498007, # degrees
    'elevation': 100.0       # meters
}

# GUI Configuration
GUI = {
    'window_title': 'BVEX Ground Station with Spectrometer',
    'window_size': (1600, 900),  # Increased window size to accommodate spectra
    'update_interval': 1000,  # ms for GUI updates
    'sky_chart_size': (6, 6),  # inches - reduced from (10, 10)
    'gps_panel_width': 280,    # reduced from 350
    'spectra_panel_size': (8, 6)  # inches for spectra plot
}

# Celestial Objects to Display
CELESTIAL_OBJECTS = {
    'solar_system': ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune'],
    'targets': {
        'W49N': {'ra': '19h11m28.37s', 'dec': '09d06m02.2s'}
    }
} 
 
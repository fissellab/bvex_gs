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
    'window_title': 'BVEX Ground Station',
    'window_size': (1400, 800),
    'update_interval': 1000,  # ms for GUI updates
    'sky_chart_size': (10, 10),  # inches
    'gps_panel_width': 350
}

# Celestial Objects to Display
CELESTIAL_OBJECTS = {
    'solar_system': ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune'],
    'targets': {
        'W49N': {'ra': '19h11m28.37s', 'dec': '09d06m02.2s'}
    }
} 
 
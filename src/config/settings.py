"""
BVEX Ground Station Configuration Settings
"""

# GPS Server Configuration
GPS_SERVER = {
    'host': '100.70.234.8',
    'port': 8080,  # You'll need to verify this port
    'request_message': 'GET_GPS',
    'timeout': 5.0,
    'update_interval': 1.0  # 1 second between requests (1 Hz)
}

# Ophiuchus Server Configuration
OPH_SERVER = {
    'host': '100.85.84.122',
    'port': 8002,  # You'll need to verify this port
    'timeout': 1.0,  # Increased from 0.1s to 1.0s for more reliable connections
    'update_interval': 0.1  # Keep 10Hz base rate but with better timeout
}

# BCP Spectrometer Configuration
BCP_SPECTROMETER = {
    'host': '100.70.234.8',  # Saggitarius system IP
    'port': 8081,
    'timeout': 5.0,
    'update_interval': 1.0   # 1 second = 1 Hz updates
}

# Star Camera Configuration
STAR_CAMERA = {
    'host': '100.85.84.122',  # Star camera system IP - update this with correct IP
    'port': 8001,
    'timeout': 10.0,  # Longer timeout for image transfers
    'update_interval': 10.0   # 10 seconds between image requests due to bandwidth limits
}

# PR59 Temperature Controller Configuration
PR59_SERVER = {
    'host': '100.70.234.8',  # BCP system IP (same as spectrometer)
    'port': 8082,
    'timeout': 2.0,
    'update_interval': 1.0   # 1 second between requests
}

# Heater System Configuration
HEATER_SERVER = {
    'host': '172.20.4.178',  # LabJack T7 IP address as specified in the guide
    'port': 8006,
    'timeout': 2.0,  # 2 second timeout as suggested in the guide  
    'update_interval': 2.0   # 2 second between requests (relay toggles don't need frequent updates)
}

# Heater Telemetry Configuration (new - from guide)
HEATER_TELEMETRY = {
    'host': 'localhost',  # Telemetry server host
    'port': 8081,  # Telemetry server port as specified in guide
    'timeout': 2.0,
    'update_interval': 2.0
}

# GPS Data Processing
GPS_PROCESSING = {
    'heading_offset': 0.0,  # degrees - constant offset to add to GPS heading
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
    'window_title': 'BVEX Ground Station with Spectrometer and Star Camera',
    'window_size': (1800, 950),  # Increased window size to accommodate star camera
    'update_interval': 100,  # ms for GUI updates
    'sky_chart_size': (10, 10),  # inches - increased for better visibility
    'gps_panel_width': 280,    # reduced from 350
    'spectra_panel_size': (8, 6),  # inches for spectra plot
    'lazisusan_enabled': 1
}

# Celestial Objects to Display
CELESTIAL_OBJECTS = {
    'solar_system': ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune'],
    'line': {
        'W49N': {'ra': '19h11m28.37s', 'dec': '09d06m02.2s'},
        'Orion KL': {'ra':'05h35m14.16s', 'dec':'-05d22m21.5s'}
    },
    'continuum': {
        '3C 273': {'ra':'12h29m6.7s','dec':'02d03m09s'},
        '3C 279': {'ra':'12h56m11.1s','dec':'-05d47m22s'},
        '3C 454.3': {'ra':'22h53m57.7s','dec':'16d08m53.6s'},
        '4C 11.69': {'ra': '22h32m36.4s','dec':'11d43m50.9s'},
        '3C 84': {'ra': '03h19m48.2s','dec':'41d30m42.1s'}
    }
} 
 

# BVEX Ground Station

ground station GUI software for the Balloon-borne VLBI Experiment (BVEX). This application provides real-time information for BVEX on a GUI.

## Features

- **Real-time Sky Chart**: Interactive polar plot showing celestial objects, coordinate grids, and observation targets
- **GPS Data Display**: Live GPS coordinates (latitude, longitude, altitude, heading) with connection status
- **Professional Interface**: Clean PyQt6-based GUI with resizable panels and menu system
- **Network Communication**: UDP client for receiving data from flight computers
- **Extensible Architecture**: Modular design for easy addition of new telemetry data types

## Project Structure

```
bvex_ground_station/
├── src/
│   ├── config/              # Configuration settings
│   │   ├── __init__.py
│   │   └── settings.py      # GPS server, GUI, and observatory settings
│   ├── data/               # Data management and communication
│   │   ├── __init__.py
│   │   ├── gps_client.py   # Python UDP GPS client
│   │   └── data_manager.py # (Future: data logging and management)
│   └── gui/                # User interface components
│       ├── __init__.py
│       ├── main_window.py       # Main application window
│       ├── sky_chart_widget.py  # Sky chart display widget
│       └── gps_display_widget.py # GPS data display widget
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── gps_server.c           # Original C GPS client (reference)
├── gps_server.h           # GPS data structure definitions
└── bvex_pointing.py       # Original tkinter sky chart (reference)
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Dependencies

- **PyQt6**: Modern GUI framework
- **matplotlib**: Scientific plotting for sky charts
- **numpy**: Numerical computations
- **astropy**: Astronomical calculations and coordinate transformations

## Configuration

Edit `src/config/settings.py` to configure:

- **GPS Server**: IP address and port of the flight computer GPS server
- **Observatory Location**: Default latitude/longitude coordinates
- **GUI Settings**: Window size, update intervals, panel sizes
- **Celestial Objects**: Solar system objects and observation targets to display

### GPS Server Configuration

```python
GPS_SERVER = {
    'host': '100.70.234.8',  # Your GPS server IP
    'port': 12345,           # GPS server port
    'request_message': 'GET_GPS',
    'timeout': 5.0,
    'update_interval': 0.05  # 50ms between requests
}
```

## Usage

### Running the Application

```bash
python main.py
```

### GUI Controls

- **File Menu**:
  - Connect/Disconnect GPS: Manual control of GPS client connection
  - Exit: Close the application

- **View Menu**:
  - Refresh Sky Chart: Force update of celestial positions

- **Help Menu**:
  - About: Application information

### Interface Layout

- **Left Panel**: Real-time sky chart showing:
  - Coordinate grid (RA/Dec lines)
  - Solar system objects (Sun, Moon, planets)
  - Observation targets (W49N, etc.)
  - Current time and location

- **Right Panel**: GPS data display showing:
  - Connection status indicator
  - Latitude/Longitude with cardinal directions
  - Altitude in meters
  - Heading with compass direction
  - Last update timestamp

### GPS Data Format

The application expects GPS data in the following UDP message format:
```
gps_lat:44.224372,gps_lon:-76.498007,gps_alt:100.0,gps_head:270.0
```

## Development

### Adding New Telemetry Data

1. **Extend Data Structures**: Add new fields to data classes in `src/data/`
2. **Create Display Widgets**: Add new GUI components in `src/gui/`
3. **Update Main Window**: Integrate new widgets in `src/gui/main_window.py`
4. **Configure Settings**: Add new parameters to `src/config/settings.py`

### Architecture Notes

- **Thread Safety**: GPS client runs in separate thread with proper locking
- **Modular Design**: Each component is loosely coupled for easy testing and extension
- **Configuration-Driven**: Most parameters are externalized to settings file
- **Error Handling**: Robust error handling with logging throughout

## Troubleshooting

### GPS Connection Issues

1. Verify server IP and port in `settings.py`
2. Check network connectivity to GPS server
3. Ensure GPS server is running and responding to UDP requests
4. Check firewall settings

### Sky Chart Issues

1. Verify astropy installation for astronomical calculations
2. Check system time for accurate celestial positions
3. Ensure valid GPS coordinates for location-based calculations

### Performance Issues

1. Adjust update intervals in `settings.py`
2. Reduce sky chart size for lower-spec systems
3. Check system resources and close unnecessary applications

## License

This software is developed for the BVEX (Balloon-borne VLBI Experiment) project.

## Support

For technical support and bug reports, please contact the BVEX development team. 
 

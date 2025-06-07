# BVEX Ground Station

Professional ground station GUI software for the Balloon-borne VLBI Experiment (BVEX). This application provides a comprehensive real-time monitoring and control interface for BVEX operations.

## Current Status

The BVEX Ground Station is a fully functional PyQt6-based application that integrates multiple data sources and display systems. The software provides real-time visualization of astronomical data, GPS telemetry, and spectrometer measurements in a professional three-panel interface.

## Core Features

### Real-time Sky Chart Display
- Interactive polar coordinate sky chart with celestial object tracking
- Live coordinate grid display (RA/Dec lines with hour/degree annotations)
- Solar system object visualization (Sun, Moon, planets with distinct markers)
- Observation target tracking (W49N radio source)
- User-controlled on/off toggle with static and animated modes
- Location-aware calculations using GPS coordinates when available
- Automatic time-based updates every second during active mode

### GPS Telemetry System
- Real-time GPS data acquisition via UDP client
- Thread-safe data processing with automatic error handling
- Live display of latitude, longitude, altitude, and heading
- Coordinate system conversion and offset corrections
- Connection status monitoring with visual indicators
- Configurable update rates and timeout handling
- Support for N/A value handling from GPS server

### BCP Spectrometer Integration
- Dual-mode spectrometer support (Standard 2048-point and High-resolution 120kHz)
- Real-time spectrum visualization with frequency axis calibration
- Integrated power monitoring with time-series plotting
- Automatic spectrometer type detection and switching
- Data rate monitoring and connection status display
- Thread-safe UDP communication with rate limiting
- Error handling for connection failures and data corruption

### Professional User Interface
- Three-panel layout optimized for operational use
- Individual component control (GPS, Sky Chart, Spectrometer)
- Real-time status indicators and connection monitoring
- Resizable interface with minimum size constraints
- Menu system with connection controls and refresh options
- Status bar with permanent connection status displays

### Network Communication
- Robust UDP client implementations for multiple data sources
- Configurable server addresses and ports
- Automatic reconnection and error recovery
- Thread-safe data handling with proper synchronization
- Timeout handling and connection status reporting

## Project Architecture

```
bvex_gs/
├── src/
│   ├── config/
│   │   ├── settings.py          # Centralized configuration management
│   │   └── __init__.py
│   ├── data/
│   │   ├── gps_client.py        # GPS UDP client with threading
│   │   ├── bcp_spectrometer_client.py  # Spectrometer UDP client
│   │   └── __init__.py
│   └── gui/
│       ├── main_window.py       # Main application window
│       ├── sky_chart_widget.py  # Astronomical sky chart display
│       ├── gps_display_widget.py    # GPS data visualization
│       ├── spectra_display_widget.py # Spectrometer data display
│       └── __init__.py
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── bvex_pointing.py            # Legacy tkinter implementation (reference)
├── gps_server.c                # GPS server C implementation
├── gps_server.h                # GPS data structure definitions
├── BCP_CLIENT_GUIDE.md         # Comprehensive spectrometer client guide
└── README.md                   # This documentation
```

## Technical Specifications

### Dependencies
- **PyQt6 >= 6.4.0**: Modern GUI framework with native look and feel
- **matplotlib >= 3.6.0**: Scientific plotting for sky charts and spectra
- **numpy >= 1.24.0**: Numerical computations and data processing
- **astropy >= 5.2.0**: Astronomical calculations and coordinate transformations

### Network Configuration
- **GPS Server**: UDP communication on configurable IP/port (default: 100.70.234.8:8080)
- **BCP Spectrometer**: UDP communication on configurable IP/port (default: 100.70.234.8:8081)
- **Protocol**: Custom message formats with error handling and validation

### Data Processing
- **GPS Data**: Real-time parsing with coordinate offsets and heading corrections
- **Astronomical Calculations**: Astropy-based coordinate transformations and ephemeris data
- **Spectrum Analysis**: Frequency domain processing with power integration
- **Time Synchronization**: UTC-based timing for all astronomical calculations

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Network connectivity to BVEX flight systems

### Installation Steps
```bash
# Clone repository
git clone [repository-url]
cd bvex_gs

# Install dependencies
pip install -r requirements.txt

# Configure settings
# Edit src/config/settings.py for your network configuration

# Run application
python main.py
```

### Configuration

Key configuration parameters in `src/config/settings.py`:

```python
# GPS Server Configuration
GPS_SERVER = {
    'host': '100.70.234.8',
    'port': 8080,
    'update_interval': 0.05  # 50ms between requests
}

# BCP Spectrometer Configuration
BCP_SPECTROMETER = {
    'host': '100.70.234.8',
    'port': 8081,
    'update_interval': 1.0   # 1 Hz updates
}

# Observatory Location (Kingston, ON area)
OBSERVATORY = {
    'latitude': 44.224372,
    'longitude': -76.498007,
    'elevation': 100.0
}
```

## Operational Usage

### Starting the Application
1. Ensure network connectivity to flight systems
2. Launch with `python main.py`
3. Use File menu to connect GPS
4. Activate Sky Chart and Spectrometer as needed

### Interface Controls
- **Sky Chart Toggle**: Turn on/off real-time astronomical display
- **GPS Connection**: Manual connect/disconnect with automatic retry
- **Spectrometer Toggle**: Activate spectrum acquisition and display
- **Status Monitoring**: Real-time connection and data rate indicators

### Data Formats

**GPS Data Format:**
```
gps_lat:44.224372,gps_lon:-76.498007,gps_alt:100.0,gps_head:270.0
```

**Spectrometer Data Formats:**
- Standard: `SPECTRA_STD:timestamp:1673123456.789,points:2048,data:1.234,5.678,...`
- High-res: `SPECTRA_120KHZ:timestamp:1673123456.789,points:167,freq_start:22.225,freq_end:22.245,baseline:-45.2,data:1.234,5.678,...`

## Development Status

### Completed Features
- Full GUI implementation with professional layout
- Complete GPS telemetry integration
- BCP spectrometer data acquisition and visualization
- Real-time astronomical calculations and display
- Robust network communication with error handling
- Comprehensive configuration management
- Thread-safe data processing

### Architecture Highlights
- Modular design with clear separation of concerns
- Thread-safe implementation for real-time data handling
- Configurable parameters for different deployment scenarios
- Professional Qt-based interface suitable for operational use
- Comprehensive error handling and logging throughout

### Extension Points
- Additional telemetry data sources can be integrated via similar client patterns
- New visualization widgets can be added to the main window layout
- Configuration system supports easy addition of new parameters
- Logging system provides debugging and operational monitoring

## Troubleshooting

### Common Issues
1. **GPS Connection Failures**: Verify network connectivity and server IP/port configuration
2. **Spectrometer Data Issues**: Check spectrometer server status and request rate limits
3. **Sky Chart Performance**: Adjust update intervals for system performance
4. **Display Issues**: Ensure proper PyQt6 installation and graphics drivers

### Debug Information
- Application logging provides detailed operational information
- Status bar displays real-time connection status
- Individual component toggles allow isolation of issues
- Configuration file allows adjustment of timeouts and retry parameters

## Support

This software is developed for the BVEX (Balloon-borne VLBI Experiment) project. The system provides real-time ground station capabilities for balloon-borne radio astronomy operations. 
 

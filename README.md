# BVEX Ground Station

Professional ground station GUI software for the Balloon-borne VLBI Experiment (BVEX). This application provides a comprehensive real-time monitoring and control interface for BVEX operations.

## Current Status

The BVEX Ground Station is a fully functional PyQt6-based application that integrates multiple data sources and display systems. The software provides real-time visualization of astronomical data, GPS telemetry, spectrometer measurements, and star camera images in a professional four-panel interface.

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

### Star Camera Image Display
- Real-time star camera image acquisition via UDP downlink protocol
- JPEG image compression and decompression with quality control
- Bandwidth-limited image updates (every 10 seconds at ~200 kB/s)
- Image metadata display (dimensions, compression quality, detected stars)
- Server status monitoring (queue size, bandwidth usage, transmission status)
- Thread-safe image downloading with progress tracking
- Automatic image scaling and display with scroll support

### Professional User Interface
- Four-panel layout optimized for operational use
- Individual component control (GPS, Sky Chart, Spectrometer, Star Camera)
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
│   │   ├── star_camera_client.py    # Star camera UDP client
│   │   └── __init__.py
│   └── gui/
│       ├── main_window.py       # Main application window
│       ├── sky_chart_widget.py  # Astronomical sky chart display
│       ├── gps_display_widget.py    # GPS data visualization
│       ├── spectra_display_widget.py # Spectrometer data display
│       ├── star_camera_widget.py    # Star camera image display
│       └── __init__.py
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── bvex_pointing.py            # Legacy tkinter implementation (reference)
├── gps_server.c                # GPS server C implementation
├── gps_server.h                # GPS data structure definitions
├── BCP_CLIENT_GUIDE.md         # Comprehensive spectrometer client guide
└── README.md                   # This documentation
```

## Data Logging System

### Overview
The BVEX Ground Station now features a comprehensive per-widget data logging system that replaces the previous monolithic CSV logger. This system provides timestamped session directories and widget-specific data logging with automatic cleanup.

### Key Features
- **Timestamped Session Directories**: `data/YYYY-MM-DD_HH-MM-SS_session/`
- **Per-widget Data Logging**: Each instrument has its own dedicated logger
- **Complete Spectra Logging**: Full 2048-point spectrometer data with timestamps
- **Image Saving**: Star camera images saved as JPEG at 100% quality
- **PBoB Logging**: Power distribution box relay states and current measurements
- **Single Toggle Control**: One button in HousekeepingWindow controls all logging
- **Active State Checking**: Only logs data when widgets are turned ON

### Supported Loggers
1. **GPS Data Logger** - Position and telemetry data
2. **Spectrometer Logger** - Complete 2048-point spectra with timestamps
3. **Star Camera Logger** - Image metadata and actual image files
4. **Motor Controller Logger** - Motor positions and status
5. **PR59 Logger** - Temperature controller data
6. **Heater Logger** - Heater system relay states and temperatures
7. **PBoB Logger** - Power distribution box relay states and currents
8. **Ophiuchus Logger** - Integrated telescope telemetry

### File Structure
```
data/
└── 2025-07-27_00-01-47_session/
    ├── gps_data.csv
    ├── spectrometer_data.csv
    ├── star_camera_data.csv
    ├── motor_controller_data.csv
    ├── pr59_temperature_data.csv
    ├── heater_system_data.csv
    ├── pbob_data.csv
    ├── ophiuchus_data.csv
    └── star_camera/
        ├── image_20250727_000100.jpg
        ├── image_20250727_000110.jpg
        └── thumbnails/
```

### Usage
- **Start Logging**: Toggle "Start Data Logging" in HousekeepingWindow
- **Session Management**: Automatic creation and cleanup of old sessions
- **Data Access**: All files accessible via session directory or through UI

## Technical Specifications

### Dependencies
- **PyQt6 >= 6.4.0**: Modern GUI framework with native look and feel
- **matplotlib >= 3.6.0**: Scientific plotting for sky charts and spectra
- **numpy >= 1.24.0**: Numerical computations and data processing
- **astropy >= 5.2.0**: Astronomical calculations and coordinate transformations
- **Pillow >= 9.0.0**: Image processing for star camera JPEG handling

### Network Configuration
- **GPS Server**: UDP communication on configurable IP/port (default: 100.70.234.8:8080)
- **BCP Spectrometer**: UDP communication on configurable IP/port (default: 100.70.234.8:8081)
- **Star Camera**: UDP communication on configurable IP/port (default: 100.70.234.8:8001)
- **PBoB System**: UDP communication via Ophiuchus server (default: 100.85.84.122:8002)
- **Protocol**: Custom message formats with error handling and validation

### Data Processing
- **GPS Data**: Real-time parsing with coordinate offsets and heading corrections
- **Astronomical Calculations**: Astropy-based coordinate transformations and ephemeris data
- **Spectrum Analysis**: Frequency domain processing with power integration
- **Time Synchronization**: UTC-based timing for all astronomical calculations
- **Data Logging**: Real-time collection and storage of all instrument data

## Installation and Setup

### Prerequisites
- **Python 3.8 or higher** (Python 3.9+ recommended)
- **pip package manager** (usually included with Python)
- **Network connectivity** to BVEX flight systems

### Quick Setup (Recommended)

We **highly recommend** using a virtual environment to avoid dependency conflicts with your system Python packages.

#### Option 1: Automated Setup (Easiest)

```bash
# Clone repository
git clone [repository-url]
cd bvex_gs

# Run automated setup script
./setup.sh
```

The automated script will:
- ✅ Check Python version compatibility
- ✅ Create a virtual environment (`venv/`)
- ✅ Install all dependencies automatically
- ✅ Provide clear next steps

#### Option 2: Manual Setup

```bash
# Clone repository
git clone [repository-url]
cd bvex_gs

# Create virtual environment
python3 -m venv bvex_gs_env

# Activate virtual environment
source bvex_gs_env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Daily Usage

After initial setup, to run the application:

```bash
cd bvex_gs
source bvex_gs_env/bin/activate  # Activate virtual environment
python main.py            # Run application
deactivate                # When done (optional)
```


### Virtual Environment Management

**Check if virtual environment is active:**
- Your terminal prompt should show `(venv)` at the beginning
- Run `which python` - it should point to the venv directory

**Deactivate virtual environment:**
```bash
deactivate
```

**Remove virtual environment (if needed):**
```bash
rm -rf venv
```

**Recreate virtual environment:**
```bash
# Just run the setup script again
./setup.sh
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

# Star Camera Configuration
STAR_CAMERA = {
    'host': '100.70.234.8',
    'port': 8001,
    'update_interval': 10.0  # 10 second intervals due to bandwidth limits
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
- **Star Camera Toggle**: Activate image acquisition every 10 seconds
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

### Common Installation Issues

**1. Python Version Problems:**
```bash
# Check your Python version
python3 --version

# If version is < 3.8, install newer Python
```

**2. Virtual Environment Activation Issues:**
```bash
# If activation fails, try:
python3 -m venv --clear bvex_gs_env
source bvex_gs_env/bin/activate
```

**3. Permission Errors:**
```bash
# If setup.sh won't run
chmod +x setup.sh
./setup.sh
```

**4. PyQt6 Installation Issues:**
```bash
# If PyQt6 fails to install, try:
pip install --upgrade pip setuptools wheel
pip install PyQt6
```

**5. "Module not found" errors:**
- Make sure virtual environment is activated (you should see `(venv)` in your prompt)
- Re-run the setup script to ensure all dependencies are installed

### Common Runtime Issues
1. **GPS Connection Failures**: Verify network connectivity and server IP/port configuration
2. **Spectrometer Data Issues**: Check spectrometer server status and request rate limits  
3. **Sky Chart Performance**: Adjust update intervals for system performance
4. **Star Camera Connection**: Verify Ophiuchus server is running on 100.85.84.122:8002
5. **Display Issues**: Ensure proper PyQt6 installation and graphics drivers

### Debug Information
- Application logging provides detailed operational information
- Status bar displays real-time connection status
- Individual component toggles allow isolation of issues
- Configuration file allows adjustment of timeouts and retry parameters

## Support

This software is developed for the BVEX (Balloon-borne VLBI Experiment) project. The system provides real-time ground station capabilities for balloon-borne radio astronomy operations. 
 

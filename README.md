# BVEX Ground Station

Professional ground station software for the Balloon-borne VLBI Experiment (BVEX). A comprehensive PyQt6-based multi-window application providing real-time monitoring and control of balloon-borne astronomical instruments during flight operations.

## System Overview

The BVEX Ground Station represents a complete operational platform for balloon-based radio astronomy, featuring a distributed three-window architecture optimized for field operations. The system integrates multiple data sources, provides real-time scientific visualization, and maintains comprehensive data logging for post-flight analysis.

### Key Capabilities

- **Multi-instrument telemetry acquisition** (10+ concurrent data streams)
- **Real-time scientific visualization** with professional-grade displays
- **Comprehensive data logging** with timestamped session management
- **Distributed window architecture** for optimal screen utilization
- **Automated installation** with Ubuntu 24.04 LTS optimization
- **Network-resilient operation** with automatic reconnection

## Architecture

### Multi-Window Design (v2.0+)

The application employs a **three-window architecture** that maximizes operational efficiency:

1. **Pointing Window** - Telescope pointing operations and celestial navigation
2. **Telescope Data Window** - Scientific instrument monitoring and data acquisition  
3. **Housekeeping Window** - System monitoring, data logging, and environmental controls

Each window operates independently with dedicated network connections and can be positioned across multiple monitors for optimal workflow.

### Data Sources & Network Configuration

| System | IP Address | Port | Description |
|--------|------------|------|-------------|
| **GPS Telemetry** | 100.70.234.8 | 8080 | Real-time GPS coordinates and heading |
| **BCP Spectrometer** | 100.70.234.8 | 8081 | Dual-mode radio spectrometer data |
| **General Telemetry** | 100.70.234.8 | 8082 | PR59, VLBI, and Aquila backend data |
| **Star Camera** | 100.85.84.122 | 8001 | Star field imaging with JPEG compression |
| **BCP Housekeeping** | 100.85.84.122 | 8002 | Environmental sensors and system status |
| **Heater Control** | 172.20.4.178 | 8006 | LabJack T7 heater system interface |

### Core System Components

#### Data Acquisition Layer (`src/data/`)

**Primary Network Clients:**
- `gps_client.py` - GPS telemetry with coordinate offset corrections
- `bcp_spectrometer_client.py` - Dual-mode radio spectrometer (2048-point standard + 120kHz high-resolution)
- `star_camera_client.py` - Star camera images via UDP with bandwidth management
- `pr59_client.py` - Temperature controller for PR59 calibration system
- `heater_client.py` - LabJack T7-based heater system control
- `housekeeping_client.py` - BCP environmental monitoring (10+ temperature sensors)
- `system_monitor_client.py` - Flight computer health metrics (CPU, memory, storage)
- `ticc_client.py` - Timing instrument correlation data
- `vlbi_client.py` - VLBI backend telemetry and status
- `aquila_client.py` - Aquila backend data acquisition

**Data Management:**
- `session_manager.py` - Timestamped session creation and cleanup
- `data_logging_orchestrator.py` - Centralized logging control across all instruments
- `widget_data_logger.py` - Per-widget data logging with CSV output
- `image_data_logger.py` - Star camera image archival with thumbnail generation

#### User Interface Layer (`src/gui/`)

**Pointing Window Components:**
- `sky_chart_widget.py` - Real-time polar coordinate sky chart with celestial object tracking
- `star_camera_widget.py` - Live star camera display with contrast enhancement
- `gps_display_widget.py` - GPS coordinates with configurable offset corrections
- `motor_controller_widget.py` - Telescope pointing and scanning control
- `scanning_operations_widget.py` - Automated observation modes and raster scans

**Telescope Data Window Components:**
- `spectra_display_widget.py` - Real-time spectrum visualization with frequency calibration
- `vlbi_telemetry_widget.py` - VLBI backend status and correlation data
- `ticc_widget.py` - Timing instrument control and monitoring
- `backend_status_widget.py` - Aquila backend system health and performance

**Housekeeping Window Components:**
- `housekeeping_widget.py` - BCP environmental sensors and system status
- `pr59_widget.py` - Temperature controller interface and monitoring
- `heater_widget.py` - Heater system control with relay status
- `pbob_widget.py` - Power distribution box monitoring and control
- `system_monitor_widget.py` - Flight computer resource monitoring
- `network_traffic_widget.py` - Network connectivity and bandwidth monitoring

## Data Logging System

### Session-Based Architecture

The system implements a comprehensive **per-widget data logging system** with automatic session management:

**Session Structure:**
```
data/
└── 2025-08-16_14-30-45_session/
    ├── gps_data.csv                    # GPS telemetry
    ├── spectrometer_data.csv          # Complete 2048-point spectra
    ├── star_camera_data.csv           # Image metadata and timestamps
    ├── motor_controller_data.csv      # Telescope positions and status
    ├── pr59_temperature_data.csv      # PR59 temperature readings
    ├── heater_system_data.csv         # Heater states and temperatures
    ├── pbob_data.csv                  # Power distribution data
    ├── ophiuchus_data.csv             # Integrated system telemetry
    ├── system_monitor_data.csv        # Computer health metrics
    └── star_camera_images/
        ├── image_20250816_143045.jpg  # Full-resolution star images
        ├── image_20250816_143055.jpg
        └── thumbnails/                # Quick-look thumbnails
```

**Logging Control:**
- **Single-toggle activation** via HousekeepingWindow
- **Per-widget activation** - only logs when instruments are enabled
- **Automatic cleanup** - sessions older than 30 days removed
- **Real-time monitoring** - logging status visible in GUI

**Supported Data Types:**
1. **GPS Data** - Position, altitude, heading, and quality metrics
2. **Spectrometer Data** - Full 2048-point spectra with timestamps and calibration
3. **Star Camera** - JPEG images (100% quality) with metadata and thumbnails
4. **Motor Controller** - Azimuth/elevation positions and movement status
5. **PR59 Temperature** - 8-channel temperature readings with alarm states
6. **Heater System** - Relay states, temperatures, and control commands
7. **PBoB Power** - Relay states, current measurements, and voltage monitoring
8. **Ophiuchus Telemetry** - Integrated system health and environmental data
9. **System Monitor** - CPU usage, memory consumption, and disk space
10. **BCP Housekeeping** - Environmental sensors, pressure readings, and system alerts

## Installation & Setup

### Prerequisites
- **Python 3.8+** (Python 3.9+ recommended)
- **Network connectivity** to BVEX flight systems
- **Ubuntu 24.04 LTS** (optimized) or equivalent Linux distribution
- **Multi-monitor setup** recommended for optimal workflow

### Automated Setup (Ubuntu 24.04 LTS - Highly Recommended)

The automated setup script provides complete system configuration optimized for Ubuntu 24.04 LTS:

```bash
# Clone repository
git clone [repository-url]
cd bvex_gs

# Make setup script executable
chmod +x setup.sh

# Run automated setup
./setup.sh
```

**Setup Script Features:**
- ✅ **System detection** - Ubuntu 24.04 LTS optimization
- ✅ **Dependency installation** - Qt6, PyQt6, scientific libraries
- ✅ **Virtual environment** - Isolated `bvex_gs_env` creation
- ✅ **Qt6 configuration** - Platform-specific optimizations
- ✅ **Network testing** - Connectivity validation
- ✅ **Installation verification** - Comprehensive testing

### Manual Setup (Cross-Platform)

For non-Ubuntu systems or custom configurations:

```bash
# Create virtual environment
python3 -m venv bvex_gs_env

# Activate environment
source bvex_gs_env/bin/activate  # Linux/Mac
# or
bvex_gs_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Launch application
python main.py
```

### Daily Operation

```bash
# Activate environment
source bvex_gs_env/bin/activate

# Launch multi-window interface
python main.py

# Three windows will automatically open and position:
# 1. Pointing Window (left monitor/position)
# 2. Telescope Data Window (center/right)  
# 3. Housekeeping Window (far right/data station)
```

## Configuration

### Network Settings (`src/config/settings.py`)

Key configuration parameters can be modified for different deployment scenarios:

```python
# GPS Configuration
GPS_SERVER = {
    'host': '100.70.234.8',
    'port': 8080,
    'update_interval': 1.0,  # 1 Hz updates
    'timeout': 5.0
}

# Observatory Location (Kingston, ON)
OBSERVATORY = {
    'latitude': 44.224372,
    'longitude': -76.498007,
    'elevation': 100.0
}

# Star Camera Settings
STAR_CAMERA = {
    'host': '100.85.84.122',
    'port': 8001,
    'update_interval': 10.0,  # 10 seconds for bandwidth management
    'timeout': 10.0
}
```

### GUI Configuration
- **Window positioning** - Automatic across available screens
- **Update intervals** - Configurable per instrument
- **Display quality** - Optimized for scientific visualization
- **Network timeouts** - Robust error handling

## Operational Usage

### Starting the System
1. **Network verification** - Ensure connectivity to all BVEX systems
2. **Environment activation** - `source bvex_gs_env/bin/activate`
3. **Application launch** - `python main.py`
4. **Window arrangement** - Position across monitors as desired
5. **Instrument activation** - Use individual window controls
6. **Data logging** - Enable via HousekeepingWindow toggle

### Interface Controls

**Pointing Window:**
- **Sky Chart** - Real-time celestial display with object tracking
- **Star Camera** - Live imagery with 10-second updates
- **GPS Display** - Coordinate monitoring with offset correction
- **Motor Control** - Manual and automated telescope pointing
- **Scanning Operations** - Programmed observation patterns

**Telescope Data Window:**
- **Spectrometer** - Real-time spectrum acquisition and display
- **VLBI Telemetry** - Backend correlation and timing data
- **TICC Interface** - Timing system control and monitoring
- **Backend Status** - Aquila system health indicators

**Housekeeping Window:**
- **Data Logging Control** - Single toggle for all instruments
- **Environmental Monitoring** - BCP temperature and pressure sensors
- **PR59 Temperature** - 8-channel calibration system monitoring
- **Heater Control** - LabJack T7 relay and temperature management
- **Power Distribution** - PBoB relay states and current monitoring
- **System Health** - Flight computer resource utilization
- **Network Status** - Connectivity and bandwidth monitoring

### Data Access

**Real-time Display:**
- Live widget updates with configurable refresh rates
- Color-coded status indicators for quick assessment
- Warning/alarm states with visual alerts
- Network connectivity status for all instruments

**Logged Data:**
- **CSV exports** for all instrument data with timestamps
- **Image archives** with full-resolution star camera data
- **Session directories** organized by date/time
- **Thumbnail generation** for quick image review
- **Automated cleanup** maintaining 30-day retention

## Troubleshooting

### Common Installation Issues

**Qt6 Display Problems:**
```bash
# Ensure system packages are installed
sudo apt update
sudo apt install qt6-base-dev libqt6gui6 libqt6widgets6

# Force X11 platform (if Wayland issues)
export QT_QPA_PLATFORM=xcb
```

**Network Connectivity:**
```bash
# Test individual connections
telnet 100.70.234.8 8080    # GPS
telnet 100.85.84.122 8001   # Star camera
ping 100.70.234.8          # General connectivity
```

**Virtual Environment Issues:**
```bash
# Recreate environment if corrupted
rm -rf bvex_gs_env
./setup.sh

# Verify activation
which python  # Should show bvex_gs_env path
```

**Python Version Problems:**
```bash
# Check version
python3 --version  # Must be 3.8+

# Ubuntu 24.04 users: ensure system Python
sudo apt install python3 python3-venv python3-pip
```

### Runtime Issues

**Connection Failures:**
1. **Verify IP addresses** in `src/config/settings.py`
2. **Check firewall settings** on local system
3. **Confirm server status** on BVEX flight systems
4. **Review network logs** in application log files

**Display Issues:**
1. **Multi-monitor setup** - Windows auto-position across screens
2. **Resolution problems** - Use `QT_AUTO_SCREEN_SCALE_FACTOR=1`
3. **Wayland compatibility** - Force X11 with `QT_QPA_PLATFORM=xcb`

**Data Logging Problems:**
1. **Disk space** - Ensure adequate storage for session data
2. **Permissions** - Verify write access to `data/` directory
3. **Session cleanup** - Automatic 30-day retention
4. **Logger activation** - Check individual widget toggle states

### Debug Information

**Log Files:**
- **Application logs**: `logs/bvex_ground_station_*.log`
- **Detailed debugging**: All levels logged with timestamps
- **Error tracking**: Console shows warnings and errors
- **Network diagnostics**: Connection status and retry attempts

**Configuration Files:**
- **Main settings**: `src/config/settings.py`
- **Network parameters**: Configurable IP addresses and ports
- **GUI preferences**: Window sizes and update intervals
- **Celestial objects**: Observable targets and coordinates

**Support Resources:**
- **Client guides**: `docs/` directory with protocol specifications
- **Network troubleshooting**: Built-in connectivity monitoring
- **Performance metrics**: Real-time system resource display
- **Community support**: BVEX team technical assistance

## Development & Extension

### Architecture Benefits
- **Modular design** - Easy addition of new instruments
- **Thread-safe implementation** - Concurrent data acquisition
- **Network resilience** - Automatic reconnection and error handling
- **Scalable logging** - Per-widget data management
- **Professional GUI** - Qt6-based interface suitable for field use

### Extension Points
- **New instruments** - Add via standardized client patterns
- **Custom displays** - New widgets integrate seamlessly
- **Data formats** - Extensible logging system
- **Network protocols** - UDP-based with error handling
- **Configuration system** - Centralized parameter management

This system represents a complete operational platform for balloon-borne radio astronomy, providing the BVEX team with professional-grade monitoring and control capabilities throughout flight operations.
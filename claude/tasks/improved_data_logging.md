# BVEX Ground Station - Improved Data Logging Implementation Plan

## Overview
Replace the current monolithic data logger with a flexible, per-widget data logging system that creates separate CSV files for each data type, supports dynamic data rates, organizes logs by session, and now includes **star camera image saving**.

## Current State Analysis
- **Existing Logger**: `src/data/data_logger.py` - monolithic CSV with all data types at 1Hz
- **Limitations**: 
  - Single CSV file with fixed structure
  - No support for per-widget data rates
  - No image saving capability
  - Hard-coded data collection from GUI widgets
  - Logs stored in `logs/` directory with timestamped filenames

## New Architecture Design

### 1. Directory Structure
```
data/
├── 2025-07-27_14-30-45_session/
│   ├── gps_data.csv
│   ├── spectrometer_data.csv
│   ├── star_camera_data.csv
│   ├── star_camera_images/
│   │   ├── 2025-07-27_14-30-45_0001.jpg
│   │   ├── 2025-07-27_14-30-46_0002.jpg
│   │   └── 2025-07-27_14-30-47_0003.jpg
│   ├── motor_controller_data.csv
│   ├── pr59_temperature_data.csv
│   ├── heater_system_data.csv
│   └── ophiuchus_telemetry.csv
├── 2025-07-27_15-45-12_session/
│   └── ...
```

### 2. Data Logger Classes

#### Core Classes to Implement

1. **SessionManager** (`src/data/session_manager.py`)
   - Creates timestamped session directories
   - Manages session lifecycle
   - Provides path utilities for log files and image directories

2. **WidgetDataLogger** (`src/data/widget_data_logger.py`)
   - Base class for all widget-specific loggers
   - Handles CSV file creation and writing
   - Manages data rate changes dynamically
   - Thread-safe operations

3. **ImageDataLogger** (`src/data/image_data_logger.py`)
   - Specialized logger for star camera images
   - Saves JPEG images with timestamped filenames
   - Manages image directory structure
   - Links images to CSV metadata entries

4. **Per-Widget Loggers** (in `src/data/loggers/`)
   - `gps_logger.py` - GPS coordinates and metadata
   - `spectrometer_logger.py` - Spectrum metadata and timestamps
   - `star_camera_logger.py` - Star camera telemetry and image metadata
   - `motor_logger.py` - Motor controller data
   - `pr59_logger.py` - Temperature controller data
   - `heater_logger.py` - Heater system states
   - `ophiuchus_logger.py` - Ophiuchus telemetry data

5. **DataLoggingOrchestrator** (`src/data/data_logging_orchestrator.py`)
   - Coordinates all widget loggers
   - Provides unified start/stop interface
   - Manages logging state across all widgets

### 3. Image Saving Strategy

#### Star Camera Image Management
- **Format**: JPEG with quality setting (configurable)
- **Naming**: `YYYY-MM-DD_HH-MM-SS_mmm.jpg` (timestamp + millisecond precision)
- **Storage**: Dedicated `star_camera_images/` subdirectory per session
- **Metadata**: CSV file links images with telemetry data via filename reference
- **Compression**: Configurable quality (default 85%)
- **Size**: Save original size, optionally create thumbnails

#### Image CSV Metadata
```csv
timestamp,datetime_utc,ra,dec,field_rotation,image_rotation,azimuth,altitude,exposure_time,focus_position,image_filename,image_path,image_size_bytes,image_valid,solve_status,save_status,update_rate_hz
```

### 4. Integration Points

#### Housekeeping Window Updates
- Replace existing `DataLogger` with new orchestrator
- Update toggle button to use new system
- Add image saving status indicator
- Maintain backward compatibility with existing UI

#### Star Camera Widget Modifications
- Add image saving toggle control
- Implement image rate limiting (configurable)
- Add disk space monitoring
- Display image saving statistics

### 5. Data Rate Management
- Each widget maintains its own update frequency
- Image saving has separate rate control (e.g., save every Nth image)
- Loggers adapt to widget's actual data rate
- Configurable via widget settings

## Implementation Tasks

### Phase 1: Core Infrastructure (MVP)
1. **Create SessionManager**
   - Directory creation with timestamp
   - Session metadata storage
   - Path management utilities for images and CSV

2. **Create WidgetDataLogger base class**
   - CSV file handling
   - Thread-safe writing
   - Data rate adaptation
   - Error handling and recovery

3. **Create ImageDataLogger**
   - JPEG image saving with PIL/Pillow
   - Timestamped filename generation
   - Directory structure management
   - Disk space monitoring

4. **Create DataLoggingOrchestrator**
   - Logger registration system
   - Unified start/stop control
   - Status aggregation

### Phase 2: Widget-Specific Loggers
1. **GPS Logger**
   - Log GPS coordinates, altitude, heading, validity
   - Adapt to GPS widget's update rate

2. **Spectrometer Logger**
   - Log spectrum metadata (type, timestamp, points, valid)
   - Handle varying data rates

3. **Star Camera Logger (Enhanced)**
   - Log star camera telemetry and image metadata
   - Include image availability and processing status
   - **Save actual JPEG images to disk**
   - Link images to metadata via filename references

4. **Motor Controller Logger**
   - Log motor positions, velocities, temperatures
   - Include axis operation modes and targets

5. **PR59 Logger**
   - Log temperature readings, PID parameters, power data
   - Track controller status and setpoints

6. **Heater Logger**
   - Log relay states for all 5 channels
   - Include temperature readings when available

7. **Ophiuchus Logger**
   - Log comprehensive telemetry from Ophiuchus server
   - Include star camera, motor, and scanning data

### Phase 3: Star Camera Image Integration
1. **Image Saving Configuration**
   - Configurable image quality (1-100)
   - Image rate limiting (save every N images)
   - Maximum session size limits
   - Disk space warnings

2. **Image Metadata Enhancement**
   - EXIF data preservation
   - GPS coordinates in image metadata
   - Camera settings logging

3. **Image Management Features**
   - Automatic cleanup of old sessions
   - Image preview generation
   - Batch export functionality

### Phase 4: Integration and Testing
1. **Update HousekeepingWindow**
   - Replace DataLogger with orchestrator
   - Update UI controls for image saving
   - Add logging status per widget
   - Add disk space monitoring

2. **Star Camera Widget Integration**
   - Add image saving toggle
   - Display image saving statistics
   - Add image preview capabilities
   - Implement rate limiting controls

3. **Testing and Validation**
   - Test with live star camera data
   - Verify image quality and metadata
   - Test disk space scenarios
   - Validate long-duration image logging

### Phase 5: Advanced Features
1. **Image Processing Integration**
   - Automatic thumbnail generation
   - Image quality assessment
   - Batch processing capabilities

2. **Configuration System**
   - YAML/JSON config files for logging preferences
   - Per-widget logging enable/disable
   - Custom data rate settings
   - Image quality and rate settings

3. **Real-time Monitoring**
   - Live logging status dashboard
   - Image saving progress indicators
   - Data rate monitoring
   - Disk space alerts

## File Structure

```
src/
├── data/
│   ├── __init__.py
│   ├── session_manager.py          # Session directory management
│   ├── widget_data_logger.py       # Base logger class
│   ├── image_data_logger.py        # Image saving functionality
│   ├── data_logging_orchestrator.py # Central coordinator
│   └── loggers/
│       ├── __init__.py
│       ├── gps_logger.py
│       ├── spectrometer_logger.py
│       ├── star_camera_logger.py   # Enhanced with image saving
│       ├── motor_logger.py
│       ├── pr59_logger.py
│       ├── heater_logger.py
│       └── ophiuchus_logger.py
data/
├── 2025-07-27_14-30-45_session/
│   ├── star_camera_images/
│   └── ...
```

## Data Format Specifications

### Star Camera Enhanced CSV
```csv
timestamp,datetime_utc,ra,dec,field_rotation,image_rotation,azimuth,altitude,exposure_time,focus_position,image_filename,image_path,image_size_bytes,image_width,image_height,image_quality,image_valid,solve_status,save_status,update_rate_hz
```

### Image Saving Configuration
```json
{
  "image_saving": {
    "enabled": true,
    "quality": 85,
    "rate_limit": 1,
    "max_session_size_gb": 10,
    "create_thumbnails": true,
    "thumbnail_size": [320, 240]
  }
}
```

## Error Handling Strategy

### Image-Specific Error Handling
1. **Storage Errors**
   - Disk full detection and graceful degradation
   - Permission error recovery
   - Network drive disconnection handling

2. **Image Processing Errors**
   - Corrupt image detection
   - Quality degradation alerts
   - Automatic retry with different quality settings

3. **Rate Limiting**
   - Skip images when rate exceeded
   - Alert user via GUI
   - Log skipped images in CSV

## Performance Considerations

### Image Storage
- **Compression**: JPEG quality 85% (configurable)
- **Size**: Typical star camera images ~500KB-2MB each
- **Rate**: At 1Hz, ~1.8GB per hour maximum
- **Cleanup**: Automatic session cleanup after 30 days

### Memory Management
- **Streaming writes**: Images written directly to disk
- **Buffer limits**: 100MB maximum in-memory buffer
- **Garbage collection**: Explicit cleanup of PIL objects

## Testing Strategy

### Image-Specific Tests
1. **Image Quality Tests**
   - Verify JPEG compression quality
   - Check EXIF data preservation
   - Validate image dimensions

2. **Storage Tests**
   - Disk full simulation
   - Network drive testing
   - Long-duration image logging (hours)

3. **Integration Tests**
   - End-to-end image saving with live camera
   - Session start/stop with images
   - Rate limiting verification

## Timeline

- **Phase 1**: 1-2 days (Core infrastructure + image support)
- **Phase 2**: 2-3 days (Widget loggers + image integration)
- **Phase 3**: 2-3 days (Star camera enhancement + testing)
- **Phase 4**: 1-2 days (Advanced features + monitoring)

Total estimated time: 6-10 days for complete implementation with image saving
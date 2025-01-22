# BirdsOS Route Structure

## Main Routes

### Dashboard (/)
- Main system overview
- Quick status cards
- Latest activity feed
- System health indicators

### Camera (/camera)
- Live video feed
- Recording controls
- Camera settings
- Recent recordings list

### Hardware Control (/hardware)
- GPIO status and control
- Motor controls
- Sensor readings
- Hardware diagnostics

### Configuration (/config)
- System settings
- Profile management
- Hardware configuration
- Notification settings

### Maintenance (/maintenance)
- Food level monitoring
- System maintenance
- Storage management
- Backup controls

### Analytics (/analytics)
- Activity statistics
- Bird visit data
- Feeding patterns
- Weather correlation

## API Routes

### System API (/api/v1/system)
- GET  /status
- POST /restart
- GET  /storage
- GET  /health

### Camera API (/api/v1/camera)
- GET  /stream
- POST /record/start
- POST /record/stop
- GET  /recordings
- POST /settings

### Hardware API (/api/v1/hardware)
- GET  /gpio/status
- POST /gpio/trigger
- GET  /motors/status
- POST /motors/control
- GET  /sensors/readings

### Configuration API (/api/v1/config)
- GET  /profiles
- POST /profiles
- PUT  /profiles/{id}
- GET  /settings
- PUT  /settings

### Maintenance API (/api/v1/maintenance)
- GET  /food-level
- POST /food-refill
- GET  /storage/status
- POST /backup

### Analytics API (/api/v1/analytics)
- GET  /statistics
- GET  /visits
- GET  /patterns
- GET  /weather-data

## WebSocket Routes (/ws)
- /camera-feed
- /sensor-updates
- /system-status
- /notifications 
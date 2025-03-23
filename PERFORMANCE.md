# BirdsOS Deployment Guide - Raspberry Pi 3B

## Hardware Limitations & Considerations

### Memory (1GB RAM)
- Monitor memory usage with multiple WebSocket connections
- Implement cleanup routines for unused resources
- Limit video buffer sizes
- Consider reducing default camera resolution

### Storage
- Default 10GB storage limit should be adjusted:

```python
DEFAULT_STORAGE_LIMIT = 5 1024 1024 1024 # 5GB instead of 10GB
WARNING_THRESHOLD = 0.80 # Earlier warning
```

- Use high-quality Class 10 SD card (minimum 16GB recommended)

### GPIO
- 40 GPIO pins available
- 3.3V voltage levels only
- Use hardware PWM pins for motor control
- Consider cooling solutions for multiple GPIO outputs

## Performance Optimizations

### Camera Settings

```python
    class CameraManager:
    def init(self):
    self.buffer_time = 5 # Reduced from 10s
    self.post_time = 10 # Reduced from 20s
    self.resolution = (640, 480) # Lower resolution
    self.format = 'h264' # Hardware encoding
```

### Background Tasks

```python
from threading import Timer
class OptimizedStorageManager:
def schedule_cleanup(self):
Timer(3600, self.cleanup_old_files).start() # Hourly cleanup
```

### Database Optimization

```python
import sqlite3
class ResearchData:
def init(self):
self.db_path = 'research.db'
self.init_db()
def init_db(self):
with sqlite3.connect(self.db_path) as conn:
conn.execute('''CREATE TABLE IF NOT EXISTS measurements
(timestamp INTEGER PRIMARY KEY,
sensor_triggers INTEGER,
motor_runtime REAL)''')
```

## Software Setup

### Operating System
- Use Raspberry Pi OS Lite (minimal) for better performance

### Required Packages

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv
sudo apt-get install -y libatlas-base-dev # For numpy
sudo apt-get install -y python3-rpi.gpio
```

### Python Dependencies
Create `requirements.txt`:
```text
Flask
RPi.GPIO
opencv-python-headless # Lighter than full opencv
numpy
requests # For Telegram notifications
```

### Network Configuration
```bash
sudo raspi-config
Enable:
- Camera
- SSH (for remote management)
- I2C (if using sensors)
```

## System Service Setup

Create service file at `/etc/systemd/system/birdsos.service`:
```ini
[Unit]
Description=BirdsOS Service
After=network.target
[Service]
ExecStart=/usr/bin/python3 /path/to/app.py
WorkingDirectory=/path/to/project
User=pi
Restart=always
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
```
Enable and start service:

```bash
sudo systemctl enable birdsos
sudo systemctl start birdsos
```


## Monitoring

### System Resource Monitoring
```python
import psutil
def check_system_resources():
return {
"cpu_percent": psutil.cpu_percent(),
"memory_percent": psutil.virtual_memory().percent,
"disk_percent": psutil.disk_usage('/').percent,
"temperature": get_cpu_temperature()
}
def get_cpu_temperature():
try:
with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
return float(f.read().strip()) / 1000
except:
return None
```


## Pre-deployment Checklist

1. Hardware
   - [ ] SD card installed and formatted
   - [ ] Camera module connected
   - [ ] GPIO connections verified
   - [ ] Cooling solution in place if needed

2. Software
   - [ ] OS installed and updated
   - [ ] Required packages installed
   - [ ] Python dependencies installed
   - [ ] Service file configured

3. Configuration
   - [ ] Storage limits adjusted
   - [ ] Camera settings optimized
   - [ ] Network interfaces enabled
   - [ ] Database initialized

4. Testing
   - [ ] Memory usage monitored
   - [ ] Camera functionality verified
   - [ ] GPIO operations tested
   - [ ] Service auto-restart confirmed

## Maintenance Recommendations

1. Regular Monitoring
   - Check system logs daily
   - Monitor storage usage
   - Review temperature readings
   - Verify database size

2. Periodic Tasks
   - Clean old log files
   - Backup database
   - Update system packages
   - Check SD card health

3. Performance Checks
   - Monitor memory leaks
   - Check CPU usage patterns
   - Verify camera buffer handling
   - Test GPIO responsiveness

## Troubleshooting

### Common Issues
1. High Memory Usage
   - Check WebSocket connections
   - Verify video buffer cleanup
   - Monitor Python process memory

2. Storage Problems
   - Review cleanup routines
   - Check log rotation
   - Verify database size

3. GPIO Issues
   - Verify voltage levels
   - Check pin assignments
   - Test for interference

### Debug Commands

```bash
Check service status
sudo systemctl status birdsos
View logs
journalctl -u birdsos
Monitor system resources
top
htop (if installed)
Check temperature
vcgencmd measure_temp
View GPIO status
gpio readall
```

## Notes
- Always test thoroughly with actual hardware
- Monitor performance during initial deployment
- Keep backup of SD card after successful setup
- Document any custom modifications
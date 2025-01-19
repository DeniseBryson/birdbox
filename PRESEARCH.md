# BirdBox Web Interface - Pre-Research Document

## 1. Core Features Overview

### 1.1 Storage & Statistics
- Local storage on Raspberry Pi
- Default 10GB storage limit
- Warning at 85% capacity
- Hourly statistics
- CSV export capability

```python
class StorageManager:
    DEFAULT_STORAGE_LIMIT = 10 * 1024 * 1024 * 1024  # 10GB
    WARNING_THRESHOLD = 0.85

    def check_storage(self):
        total, used, free = shutil.disk_usage("/")
        return {
            "total": total,
            "used": used,
            "free": free,
            "warning": used / total > self.WARNING_THRESHOLD
        }
```

### 1.2 Configuration Profiles
- Persistent storage
- Multiple profiles support
- Configurable parameters:
  - Motor frequencies
  - Sensor sensitivity
  - Feeding delays

```python
class ConfigProfile:
    def __init__(self):
        self.config = {
            "name": "Default",
            "motor_frequency": {
                "min": 10,
                "max": 100,
                "default": 50
            },
            "sensor_sensitivity": 0.75,
            "feeding_delay": 5  # seconds
        }
```

### 1.3 Maintenance Functions
- Food level estimation based on motor runtime
- Statistical optimization
- Manual reset with backdating capability
- Basic maintenance logging

```python
class FoodLevelEstimator:
    def __init__(self):
        self.motor_runtime = 0
        self.last_refill = datetime.now()
        self.food_per_second = 0.5  # g/s
```

### 1.4 Notifications (Telegram)
- Internet connectivity check
- Configuration via UI
- Visual status indication
- Priority levels

```python
class NotificationManager:
    def __init__(self):
        self.telegram_token = None
        self.chat_id = None

    def check_connection(self):
        try:
            return requests.get('https://api.telegram.org',
                              timeout=5).status_code == 200
        except:
            return False
```

### 1.5 Camera Integration
- Buffer: 10s before trigger
- Post-event: 20s after motor stop
- Configurable resolution
- Storage management
- Email warnings before deletion

```python
class CameraManager:
    def __init__(self):
        self.buffer_time = 10
        self.post_time = 20
        self.resolution = (1280, 720)
        self.format = 'h264'
```

### 1.6 Research Data
- CSV export functionality
- Configurable data points
- Offline availability
- Storage monitoring

```python
class ResearchData:
    data_points = {
        "timestamp": [],
        "sensor_triggers": [],
        "motor_runtime": [],
        "estimated_food": [],
        "temperature": [],
        "video_references": []
    }
```

## 2. UI Design

### 2.1 Dashboard Layout
```html
<div class="dashboard">
    <div class="stats-cards">
        <!-- Statistics Cards -->
    </div>
    <div class="charts">
        <!-- Interactive Charts -->
    </div>
    <div class="config-panel">
        <!-- Configuration Interface -->
    </div>
</div>
```

### 2.2 Responsive Design
- Mobile-first approach
- Flexible grid system
- Touch-friendly controls

## 3. Future Extensions

### 3.1 Bird Species Recognition
- TensorFlow Lite implementation
- Pre-trained MobileNet model
- Transfer learning capability
- Local inference
- Movement pre-filtering

### 3.2 Advanced Analytics
- Pattern recognition
- Behavior analysis
- Weather correlation
- Feeding optimization

## 4. Technical Requirements

### 4.1 Hardware
- Raspberry Pi
- Camera module
- GPIO sensors
- Motors
- SD card (min. 16GB recommended)

### 4.2 Software
- Python 3.7+
- Flask
- OpenCV
- TensorFlow Lite (optional)
- SQLite/JSON storage

"""
Default configuration for BirdsOS
"""

# Storage Configuration
STORAGE_LIMIT = 10 * 1024 * 1024 * 1024  # 10GB
STORAGE_WARNING_THRESHOLD = 0.85

# Camera Configuration
CAMERA_RESOLUTION = (1280, 720)
CAMERA_FRAMERATE = 30
CAMERA_FORMAT = 'h264'
CAMERA_BUFFER_TIME = 10  # seconds before trigger
CAMERA_POST_EVENT_TIME = 20  # seconds after motor stop

# Motor Configuration
MOTOR_MIN_FREQUENCY = 10
MOTOR_MAX_FREQUENCY = 100
MOTOR_DEFAULT_FREQUENCY = 50
MOTOR_PIN_1 = 18
MOTOR_PIN_2 = 23

# Sensor Configuration
OPTICAL_GATE_1_PIN = 24
OPTICAL_GATE_2_PIN = 25
SENSOR_SENSITIVITY = 0.75
FEEDING_DELAY = 5  # seconds

# Database Configuration
SQLITE_DATABASE_PATH = 'birdsos.db'
BACKUP_ENABLED = True
BACKUP_INTERVAL = 24 * 60 * 60  # 24 hours

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'birdsos.log'

# Web Interface Configuration
SECRET_KEY = 'development-key'  # Change in production
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

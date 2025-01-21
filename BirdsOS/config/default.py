"""
Default configuration settings for BirdsOS
"""

# Server settings
HOST = '0.0.0.0'
PORT = 5001
DEBUG = True
SECRET_KEY = 'development-key'  # Change in production

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'birdsos.log'

# Camera settings
CAMERA_RESOLUTION = (1280, 720)
CAMERA_FPS = 30
VIDEO_BUFFER_SECONDS = 10  # Pre/post event buffer in seconds
CAMERA_FORMAT = 'h264'

# Storage settings
MAX_STORAGE_GB = 10
STORAGE_WARNING_THRESHOLD = 0.85  # 85% of max storage
STORAGE_CLEANUP_DAYS = 30

# GPIO settings
MOTOR_PIN = 18
SENSOR_PINS = [23, 24, 25]

# Notification settings
TELEGRAM_ENABLED = False
TELEGRAM_BOT_TOKEN = None
TELEGRAM_CHAT_ID = None

# Data retention settings
DATA_RETENTION_DAYS = 30
RECORDING_RETENTION_DAYS = 7

# Research data settings
RESEARCH_DATA_INTERVAL = 3600  # 1 hour in seconds
EXPORT_FORMAT = 'csv'

# Database settings
SQLITE_DATABASE_PATH = 'birdsos.db'
BACKUP_ENABLED = True
BACKUP_INTERVAL = 24 * 60 * 60  # 24 hours

# Storage Configuration
STORAGE_LIMIT_GB = 10.0  # Maximum storage limit in gigabytes

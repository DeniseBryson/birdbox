"""
Logging configuration for BirdsOS
"""
import os
import logging.config
from features.gpio.constants import IS_RASPBERRYPI

LOG_DIR = "/var/log/birdbox" if IS_RASPBERRYPI else os.path.expanduser('./logs/birdbox_logs')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'application.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'DEBUG' #if not IS_RASPBERRYPI else 'INFO'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'ERROR'
        },
        'debug_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'DEBUG'
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['app_file', 'error_file', 'debug_file'] if not IS_RASPBERRYPI else ['app_file', 'error_file'],
            'level': 'DEBUG' if not IS_RASPBERRYPI else 'INFO'
        },
        'features.camera': {
            'level': 'DEBUG' if not IS_RASPBERRYPI else 'INFO',
            'propagate': True
        },
        'features.gpio': {
            'level': 'DEBUG' if not IS_RASPBERRYPI else 'INFO',
            'propagate': True
        },
        'features.storage': {
            'level': 'DEBUG' if not IS_RASPBERRYPI else 'INFO',
            'propagate': True
        },
        'features.birdcontrol': {
            'level': 'DEBUG' if not IS_RASPBERRYPI else 'INFO',
            'propagate': True
        }
    }
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG) 
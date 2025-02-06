"""
Logging configuration for BirdsOS
"""
import os
import logging.config
from pathlib import Path

LOG_DIR = "/var/log/birdbox"

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
            'level': 'INFO'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'ERROR'
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['app_file', 'error_file'],
            'level': 'INFO'
        },
        'features.camera': {
            'level': 'INFO',
            'propagate': True
        },
        'features.gpio': {
            'level': 'INFO',
            'propagate': True
        },
        'features.storage': {
            'level': 'INFO',
            'propagate': True
        }
    }
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG) 
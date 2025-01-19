"""
Logger utility for BirdsOS
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from config.default import LOG_LEVEL, LOG_FORMAT, LOG_FILE

def setup_logger():
    """Configure and return the application logger"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Configure logger
    logger = logging.getLogger('BirdsOS')
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Create handlers
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, LOG_FILE),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    console_handler = logging.StreamHandler()

    # Create formatters and add it to handlers
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

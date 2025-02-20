from features.birdcontrol.birdcontrol import BirdControl
import logging
from config.logging import setup_logging
import os

# Set up logging configuration
setup_logging()
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting BirdControl in standalone mode")
    try:
        control = BirdControl()
        logger.info("BirdControl initialized successfully")
        # Add any continuous operation logic here
        while True:
            # Your continuous operation code
            pass
    except Exception as e:
        logger.error(f"Error in BirdControl: {str(e)}", exc_info=True)
        raise

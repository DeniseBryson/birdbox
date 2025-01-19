"""
Hardware abstraction layer initialization
"""
import os
import logging

logger = logging.getLogger('BirdsOS')

# Determine if we're running on a Raspberry Pi
IS_RASPBERRY_PI = os.uname().nodename.startswith('raspberrypi')

if IS_RASPBERRY_PI:
    try:
        import RPi.GPIO as GPIO
        logger.info("Using real Raspberry Pi GPIO")
    except ImportError:
        from .gpio_mock import GPIOMock
        GPIO = GPIOMock()
        logger.warning("Failed to import RPi.GPIO, using mock implementation")
else:
    from .gpio_mock import GPIOMock
    GPIO = GPIOMock()
    logger.info("Not running on Raspberry Pi, using mock implementation")

__all__ = ['GPIO', 'IS_RASPBERRY_PI'] 
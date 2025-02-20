
from typing import Callable
import logging
from config.settings import PIN_CONFIG
from features.gpio.manager import gpio_manager as GPIOManager, IN, PinState
logger = logging.getLogger(__name__)

class OpticalGates:
    """
    Manages optical gate sensors for bird detection.
    """
    def __init__(self, callback: Callable[[int, PinState], None]):
        """
        Initialize optical gates with callback for state changes.
        
        Args:
            callback: Function to call when gate state changes. Takes pin number and state as arguments.
        """
        logger.info("Initializing optical gates")
        self.gate1_pin = PIN_CONFIG['OPTICAL_GATE_1_PIN']
        self.gate2_pin = PIN_CONFIG['OPTICAL_GATE_2_PIN']
        self.gate_callback = callback
        
        # Initialize GPIO pins
        GPIOManager.configure_pin(self.gate1_pin, IN, callback=self.gate_callback)
        GPIOManager.configure_pin(self.gate2_pin, IN, callback=self.gate_callback)
        logger.info(f"Optical gates initialized with pins {self.gate1_pin} and {self.gate2_pin}")

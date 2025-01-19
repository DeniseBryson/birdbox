"""
Mock implementation of GPIO functionality for development
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger('BirdsOS')

class GPIOMock:
    """Mock GPIO implementation for development and testing"""
    
    # GPIO Mode constants
    BCM = "BCM"
    BOARD = "BOARD"
    
    # Pin states
    HIGH = 1
    LOW = 0
    
    # Pin modes
    OUT = "OUT"
    IN = "IN"
    
    def __init__(self):
        self.mode: Optional[str] = None
        self.pins: Dict[int, dict] = {}
        logger.info("Initialized GPIO Mock")
        
    def setmode(self, mode: str) -> None:
        """Set the pin numbering mode"""
        self.mode = mode
        logger.debug(f"Set GPIO mode to {mode}")
        
    def setup(self, pin: int, mode: str, initial: int = LOW) -> None:
        """Setup a GPIO pin"""
        self.pins[pin] = {
            'mode': mode,
            'state': initial,
            'event_callback': None
        }
        logger.debug(f"Setup pin {pin} as {mode} with initial state {initial}")
        
    def output(self, pin: int, state: int) -> None:
        """Set the output state of a pin"""
        if pin in self.pins:
            self.pins[pin]['state'] = state
            logger.debug(f"Set pin {pin} to state {state}")
        else:
            logger.error(f"Pin {pin} not setup")
            
    def input(self, pin: int) -> int:
        """Read the state of a pin"""
        if pin in self.pins:
            return self.pins[pin]['state']
        logger.error(f"Pin {pin} not setup")
        return self.LOW
        
    def cleanup(self) -> None:
        """Cleanup GPIO settings"""
        self.pins.clear()
        self.mode = None
        logger.debug("GPIO cleanup performed")
        
    def add_event_detect(self, pin: int, edge: str, callback=None, bouncetime=None):
        """Mock event detection setup"""
        if pin in self.pins:
            self.pins[pin]['event_callback'] = callback
            logger.debug(f"Added event detection on pin {pin}")
        
    def remove_event_detect(self, pin: int):
        """Remove event detection"""
        if pin in self.pins:
            self.pins[pin]['event_callback'] = None
            
    # Development helper methods
    def trigger_input(self, pin: int, state: int) -> None:
        """
        Development helper to simulate input changes
        """
        if pin in self.pins:
            self.pins[pin]['state'] = state
            if self.pins[pin]['event_callback']:
                self.pins[pin]['event_callback'](pin)
            logger.info(f"Triggered input on pin {pin} with state {state}")
        else:
            logger.error(f"Cannot trigger non-setup pin {pin}")
            
    def get_pin_state(self, pin: int) -> dict:
        """
        Get the current state of a pin for debugging
        """
        return self.pins.get(pin, {'error': 'Pin not setup'}) 
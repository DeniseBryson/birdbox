"""
GPIO Hardware Constants and Utilities
"""
try:
    import RPi.GPIO as RPI_GPIO
    
    def get_valid_pins():
        """Get valid GPIO pins by checking gpio_function for all possible pins."""
        valid_pins = []
        # Check all possible BCM pins (0-27 should cover all Pi models)
        for pin in range(28):
            try:
                mode = RPI_GPIO.gpio_function(pin)
                # If we can get the function, it's a valid GPIO pin
                # We exclude pins that are in special function modes
                if mode in [RPI_GPIO.IN, RPI_GPIO.OUT, RPI_GPIO.ALT0]:
                    valid_pins.append(pin)
            except (ValueError, RuntimeError):
                # Pin doesn't exist or is not a valid GPIO
                continue
        return sorted(valid_pins)
            
except ImportError:
    RPI_GPIO = None
    
    def get_valid_pins():
        """Return default valid pins for mock environment."""
        # Default pins for mock environment (40-pin header)
        return [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21]

class GPIO:
    """GPIO constants and mock implementation."""
    
    # Pin modes (match RPi.GPIO constants for consistency)
    IN = "IN"
    OUT = "OUT"
    
    # Pin states
    LOW = 0
    HIGH = 1
    
    # Mode mapping for RPi.GPIO compatibility
    MODE_MAP = {
        "IN": 1,  # RPi.GPIO.IN
        "OUT": 0  # RPi.GPIO.OUT
    }
    
    # Get valid pins dynamically
    VALID_PINS = get_valid_pins()
    
    @staticmethod
    def setup(pin: int, mode: str) -> None:
        """Mock setup for GPIO pin."""
        if pin not in GPIO.VALID_PINS:
            raise ValueError(f"Invalid GPIO pin: {pin}")
        if mode not in [GPIO.IN, GPIO.OUT]:
            raise ValueError(f"Invalid mode: {mode}")
    
    @staticmethod
    def input(pin: int) -> int:
        """Mock input for GPIO pin."""
        if pin not in GPIO.VALID_PINS:
            raise ValueError(f"Invalid GPIO pin: {pin}")
        return GPIO.LOW  # Default mock state
    
    @staticmethod
    def output(pin: int, state: int) -> None:
        """Mock output for GPIO pin."""
        if pin not in GPIO.VALID_PINS:
            raise ValueError(f"Invalid GPIO pin: {pin}")
        if state not in [GPIO.LOW, GPIO.HIGH]:
            raise ValueError(f"Invalid state: {state}")
    
    @staticmethod
    def cleanup() -> None:
        """Mock cleanup for GPIO resources."""
        pass 

def setup_input_pin(pin, edge_detection=False):
    """
    Set up a pin as input with optional edge detection.
    Pull-up/down is optional but recommended for stable readings.
    """
    if RPI_GPIO:  # Real Raspberry Pi environment
        # Basic input setup
        RPI_GPIO.setup(pin, RPI_GPIO.IN)  # Simple input setup without pull-up/down
        
        if edge_detection:
            try:
                RPI_GPIO.add_event_detect(pin, RPI_GPIO.RISING,
                                        callback=self._handle_input_change,
                                        bouncetime=200)
            except RuntimeError as e:
                logger.error(f"Failed to set up edge detection on pin {pin}: {e}")
                raise GPIOSetupError(f"Edge detection setup failed for pin {pin}. "
                                   f"Ensure valid pin number and proper permissions.")
    else:  # Mock environment
        GPIO.setup(pin, GPIO.IN) 
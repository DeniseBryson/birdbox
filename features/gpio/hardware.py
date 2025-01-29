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
    
    # Pin modes
    IN = "IN"
    OUT = "OUT"
    
    # Pin states
    LOW = 0
    HIGH = 1
    
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
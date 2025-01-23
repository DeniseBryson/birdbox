"""
GPIO Hardware Interface
"""

class GPIO:
    """Mock GPIO interface for testing."""
    
    # GPIO modes
    IN = "IN"
    OUT = "OUT"
    
    # Pin states
    HIGH = 1
    LOW = 0
    
    # Valid GPIO pins (BCM numbering)
    VALID_PINS = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26, 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21]
    
    @classmethod
    def setup(cls, pin, mode):
        """Set up a GPIO pin."""
        if pin not in cls.VALID_PINS:
            raise ValueError(f"Invalid pin number: {pin}")
        if mode not in [cls.IN, cls.OUT]:
            raise ValueError(f"Invalid mode: {mode}")
    
    @classmethod
    def output(cls, pin, state):
        """Set output state of a GPIO pin."""
        if pin not in cls.VALID_PINS:
            raise ValueError(f"Invalid pin number: {pin}")
        if state not in [cls.HIGH, cls.LOW]:
            raise ValueError(f"Invalid state: {state}")
    
    @classmethod
    def input(cls, pin):
        """Read input state of a GPIO pin."""
        if pin not in cls.VALID_PINS:
            raise ValueError(f"Invalid pin number: {pin}")
        return cls.LOW  # Mock always returns LOW for testing
    
    @classmethod
    def cleanup(cls):
        """Clean up GPIO resources."""
        pass 
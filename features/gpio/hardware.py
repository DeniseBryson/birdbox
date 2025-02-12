"""
GPIO Hardware Constants and Utilities
STABLE - Hardware interface with singleton pattern
"""
from collections.abc import Callable
import logging
from typing import Literal, Final, TypeAlias
# For real hardware
try:
    import RPi.GPIO as RPI_GPIO
except ImportError:
    raise RuntimeError("Raspberry Pi GPIO library not found")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type hints for GPIO values
PinState = Literal[0, 1, -1]  # LOW, HIGH, UNDEFINED
PinMode = Literal[0, 1]  # OUT, IN
PullUpDown = Literal[20, 21, 22]  # PUD_OFF, PUD_DOWN, PUD_UP

# GPIO Constants
HIGH: Final[PinState] = 1
LOW: Final[PinState] = 0
UNDEFINED: Final[PinState] = -1
IN: Final[PinMode] = 1
OUT: Final[PinMode] = 0
PUD_OFF: Final[PullUpDown] = 20
PUD_UP: Final[PullUpDown] = 22
PUD_DOWN: Final[PullUpDown] = 21
BOTH: Final = 33
BCM: Final = 11

# Update callback type to include both pin and state
EventCallback: TypeAlias = Callable[[int, PinState], None]

class GPIOHardware:
    """
    Manages GPIO operations with support for real Raspberry Pi hardware.
    Implements singleton pattern to ensure single point of GPIO control.
    """
    # Singleton instance
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPIOHardware, cls).__new__(cls)
        return cls._instance

    def __init__(self): 
        # Only run initialization once
        if self._initialized:
            return
            
        self._initialized = True
        self.gpio = RPI_GPIO
        self.gpio.setmode(BCM)
        logger.info("GPIO Manager initialized in BCM mode")
        self._valid_pins: list[int] | None = None  # Initialize as None, will be populated on first get_valid_pins call
        self.RPI_INFO = RPI_GPIO.RPI_INFO

    def get_valid_pins(self) -> list[int]:   
        """Get valid GPIO pins by checking gpio_function for all possible pins."""
        if self._valid_pins is not None:
            return self._valid_pins
        
        valid_pins: list[int] = []
        # Check all possible BCM pins (0-27 should cover all Pi models)
        for pin in range(100):
            try:
                mode = self.gpio.gpio_function(pin)
                # If we can get the function, it's a valid GPIO pin
                # Only include pins that can be used for input/output
                if mode in [IN, OUT]:
                    valid_pins.append(pin)
            except (ValueError, RuntimeError):
                # Pin doesn't exist or is not a valid GPIO
                continue
        
        if not valid_pins:
            raise RuntimeError("No valid pins found")
        
        self._valid_pins = sorted(valid_pins)
        logger.info(f"Valid pins found: {self._valid_pins}")
        return self._valid_pins

    def setup_input_pin(self,
                       pin: int, 
                       pull_up_down:PullUpDown=PUD_OFF, 
                       edge_detection:bool=False,
                       bouncetime:int=200,
                       callback:EventCallback|None=None
                       ):
        """
        Set up a pin as input with optional edge detection.
        Pull-up/down is optional but recommended for stable readings.

        Args:
            pin: The GPIO pin number (BCM numbering)
            pull_up_down: Pull up/down resistor setting (PUD_OFF, PUD_UP, or PUD_DOWN)
            edge_detection: Whether to enable edge detection
            bouncetime: Bounce time in ms for edge detection
            callback: Required if edge_detection is True, must not be provided if edge_detection is False.
                     Will be called with (pin, state) where state is the current pin state.
        """
        if pull_up_down not in [PUD_OFF, PUD_UP, PUD_DOWN]:
            raise ValueError("Invalid pull-up/down value")
        
        self.gpio.setup(pin, IN, pull_up_down=pull_up_down)
        pud_name = {PUD_OFF: "OFF", PUD_UP: "UP", PUD_DOWN: "DOWN"}[pull_up_down]
        logger.info(f"Setup pin {pin} as input with pull-up/pull-down value '{pud_name}'")

        if (edge_detection and not callback) or (not edge_detection and callback):
            raise ValueError("Callback must be provided with edge_detection=True and must not be provided with edge_detection=False")
        
        if edge_detection:
            try:
                # Create a wrapper that includes the pin state
                def wrapped_callback(pin: int):
                    state = self.get_pin_state(pin)
                    if callback!=None:
                        callback(pin, state)

                self.gpio.add_event_detect(
                    pin, 
                    BOTH,
                    callback=wrapped_callback,
                    bouncetime=bouncetime
                )
                logger.debug(f"Set up edge detection on pin {pin} with state-aware callback")
            except RuntimeError as e:
                logger.error(f"Failed to set up edge detection on pin {pin}: {e}")
                raise RuntimeError(f"Edge detection setup failed for pin {pin}. "
                                 f"Ensure valid pin number and proper permissions.")

    def setup_output_pin(self, pin: int, initial_state: PinState = UNDEFINED):
        """
        Set up a pin as output with optional initial state.

        Args:
            pin: The GPIO pin number (BCM numbering)
            initial_state: Initial state for the pin (HIGH or LOW), None for no initial state
        """
        if initial_state is not UNDEFINED and initial_state not in [HIGH, LOW]:
            raise ValueError("Invalid initial state, must be HIGH or LOW")
                
        self.gpio.setup(pin, OUT, pull_up_down=PUD_OFF, initial=initial_state)
        logger.info(f"Setup pin {pin} as output with initial state {initial_state}")
    
    def get_pin_state(self, pin: int) -> PinState:
        """
        Get the current state of a GPIO pin.
        """
        if pin not in self.get_valid_pins():
            raise ValueError("Invalid pin number")
        
        state = self.gpio.input(pin)

        return HIGH if state else LOW

    def set_output_state(self, pin: int, state: PinState):
        """
        Set state of pin in output mode.

        Args:
            pin: The GPIO pin number (BCM numbering)
            state: State for the pin (HIGH or LOW)
        """
        if pin not in self.get_valid_pins():
            raise ValueError("Invalid pin number")
        
        if state not in [HIGH, LOW]:
            raise ValueError("Invalid initial state, must be HIGH or LOW")

        self.gpio.output(pin, bool(state))
        logger.info(f"Set pin {pin} state to {state}")

    def cleanup(self):
        """
        Clean up all GPIO resources.
        """
        if self.gpio:
            self.gpio.cleanup()
            logger.info("GPIO resources cleaned up")
            self._initialized = False
            self._valid_pins = None  # Reset valid pins on cleanup
        else:
            logger.info("GPIO library not found, skipping cleanup")

   
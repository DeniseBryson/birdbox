"""
Mock Library for RPi.GPIO
STABLE - Mock implementation of RPi.GPIO for development and testing
"""
import logging
import os
from typing import Optional, Any, Literal

from .gpio_interface import Channel, PWMProtocol, Value, EventCallback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure logging based on environment
log_level = os.getenv('LOG_LEVEL')
if log_level is not None:
    logger.setLevel(getattr(logging, log_level.upper(), logging.ERROR))
else:
    logger.setLevel(logging.ERROR)

stream_formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)

# GPIO Mode constants - must match exactly with RPi.GPIO
BCM: Literal[11] = 11
BOARD: Literal[10] = 10
BOTH: Literal[33] = 33
FALLING: Literal[32] = 32
HARD_PWM: Literal[43] = 43
HIGH: Literal[1] = 1
I2C: Literal[42] = 42
IN: Literal[1] = 1
LOW: Literal[0] = 0
OUT: Literal[0] = 0
PUD_DOWN: Literal[21] = 21
PUD_OFF: Literal[20] = 20
PUD_UP: Literal[22] = 22
RISING: Literal[31] = 31
SERIAL: Literal[40] = 40
SPI: Literal[41] = 41
UNKNOWN: Literal[-1] = -1
VERSION: str = '0.7.0'
RPI_INFO: dict[str, Any] = {
    'MANUFACTURER': 'Sony',
    'P1_REVISION': 3,
    'PROCESSOR': 'BCM2837',
    'RAM': '1G',
    'REVISION': 'a020d3',
    'TYPE': 'Pi 3 Model B+'
}

class _MockPin:
    """Internal class to track pin state"""
    def __init__(self, number: int, mode: int = IN, pull_up_down: int = PUD_OFF, initial: int = LOW):
        self.number = number
        self.mode = mode
        self.pull_up_down = pull_up_down
        self.value = initial
        self.event_callbacks: list[EventCallback] = []
        self.edge_detect: Optional[int] = None
        self.bouncetime = -666



# Global state
_gpio_mode: Optional[Literal[10, 11]] = None
_warnings = True
_rpi3B_pins: list[int] = [2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 17, 18, 22, 23, 24, 25, 27]
_pins: dict[int, _MockPin] = {pin: _MockPin(pin) for pin in _rpi3B_pins}
logger.info(f"MockGPIO initialized with {len(_pins)} pins")

def setmode(mode: Literal[10, 11]) -> None:
    """Set up numbering mode to use for channels."""
    if mode not in [BCM, BOARD]:
        raise ValueError(f"Invalid mode: {mode}")
    _gpio_mode = mode
    logger.info(f"GPIO mode set to: {mode}")

def getmode() -> Optional[Literal[10, 11]]:
    """Get numbering mode used for channels."""
    if _gpio_mode is None:
        return None
    if _gpio_mode is BCM:
        return BCM
    if _gpio_mode is BOARD:
        return BOARD
    else:
        raise ValueError(f"Invalid mode: {_gpio_mode}")

def setup(channel: Channel, direction: int, pull_up_down: int = PUD_OFF, initial: int = -1) -> None:
    """Set up a GPIO channel or list of channels with a direction and (optional) pull/up down control."""
    
    channels = [channel] if isinstance(channel, int) else channel
    for pin in channels:
        _pins[pin] = _MockPin(pin, direction, pull_up_down, initial if initial != -1 else LOW)
        logger.info(f"Setup channel {pin} as {direction} with initial {initial} and pull_up_down {pull_up_down}")

def cleanup(channel: Optional[Channel] = None) -> None:
    """Clean up GPIO channels."""

    if channel is None:
        _pins.clear()
        _gpio_mode = None
        logger.info("Cleaning up all channels")
    else:
        channels = [channel] if isinstance(channel, int) else channel
        for pin in channels:
            _pins.pop(pin, None)
            logger.info(f"Cleaning up channel {pin}")

def input(channel: int) -> bool:
    """Read the value of a GPIO channel."""
    if channel not in _pins:
        raise RuntimeError(f"Channel {channel} not set up")
    logger.info(f"Reading from channel {channel}")
    if _pins[channel].mode == IN:
        return bool(_pins[channel].value)
    else:
        raise RuntimeError(f"Channel {channel} is not set up as an input")

def output(channel: Channel, value: Value) -> None:
    """Output to a GPIO channel or list of channels."""
    channels = [channel] if isinstance(channel, int) else channel
    values = [value] if isinstance(value, (bool, int)) else value
    
    if len(channels) != 1 and len(channels) != len(values):
        raise RuntimeError("Number of channels != number of values")
    
    for i, pin in enumerate(channels):
        if pin not in _pins.keys():
            raise RuntimeError(f"Channel {pin} not set up")
        if _pins[pin].mode != OUT:
            raise RuntimeError(f"Channel {pin} is not set up as an output")
        val = values[0] if len(values) == 1 else values[i]
        _pins[pin].value = 1 if val else 0
        logger.info(f"Output channel {pin} with value {val}")

def gpio_function(channel: int) -> int:
    """Return the current GPIO function (IN, OUT, PWM, SERIAL, I2C, SPI)."""
    if channel not in _pins.keys():
        raise ValueError(f"Channel {channel} not set up")
    return _pins[channel].mode

def add_event_detect(channel: int, edge: int, callback: Optional[EventCallback] = None, bouncetime: int = -666) -> None:
    """Enable edge detection events for a particular GPIO channel."""
    if channel not in _pins:
        raise RuntimeError(f"Channel {channel} not set up")
    _pins[channel].edge_detect = edge
    _pins[channel].bouncetime = bouncetime
    if callback:
        _pins[channel].event_callbacks.append(callback)
    logger.info(f"Event detect added for edge {edge} on channel {channel} with bounce time {bouncetime}")

def remove_event_detect(channel: int, /) -> None:
    """Remove edge detection for a particular GPIO channel."""
    if channel not in _pins:
        raise RuntimeError(f"Channel {channel} not set up")
    _pins[channel].edge_detect = None
    _pins[channel].event_callbacks.clear()
    logger.info(f"Event detect removed for channel {channel}")

def event_detected(channel: int) -> bool:
    """Returns True if an edge has occurred on a given GPIO."""
    if channel not in _pins:
        raise RuntimeError(f"Channel {channel} not set up")
    return False  # Mock always returns False for simplicity

def add_event_callback(channel: int, callback: EventCallback) -> None:
    """Add a callback for an event already defined using add_event_detect()."""
    if channel not in _pins:
        raise RuntimeError(f"Channel {channel} not set up")
    if _pins[channel].edge_detect is None:
        raise RuntimeError("Add event detection first")
    _pins[channel].event_callbacks.append(callback)
    logger.info(f"Event callback added for channel {channel}")

def wait_for_edge(channel: int, edge: int, bouncetime: int = -666, timeout: int = -1) -> Optional[int]:
    """Wait for an edge. Returns the channel number or None on timeout."""
    if channel not in _pins:
        raise RuntimeError(f"Channel {channel} not set up")
    logger.info(f"Waiting for edge {edge} on channel {channel} with bounce time {bouncetime} and timeout {timeout}")
    return None  # Mock always times out for simplicity

def setwarnings(flag: bool) -> None:
    """Enable or disable warning messages."""
    global _warnings
    _warnings = flag
    logger.info(f"Set warnings as {flag}")

class PWM(PWMProtocol):
    """Mock PWM class."""
    def __init__(self, channel: int, frequency: float) -> None:
        if channel not in _pins:
            raise RuntimeError(f"Channel {channel} not set up")
        self.channel = channel
        self.frequency = frequency
        self.dutycycle = 0.0
        logger.info(f"Initialized PWM for channel {channel} at frequency {frequency}")

    def start(self, dutycycle: float) -> None:
        """Start PWM with specified duty cycle."""
        if not 0.0 <= dutycycle <= 100.0:
            raise ValueError("Duty cycle must be between 0.0 and 100.0")
        self.dutycycle = dutycycle
        logger.info(f"Start PWM on channel {self.channel} with duty cycle {dutycycle}")

    def ChangeDutyCycle(self, dutycycle: float) -> None:
        """Change duty cycle."""
        if not 0.0 <= dutycycle <= 100.0:
            raise ValueError("Duty cycle must be between 0.0 and 100.0")
        logger.info(f"Duty cycle changed for channel {self.channel} from {self.dutycycle} to {dutycycle}")
        self.dutycycle = dutycycle

    def ChangeFrequency(self, frequency: float) -> None:
        """Change frequency."""
        if frequency <= 0.0:
            raise ValueError("Frequency must be greater than 0.0")
        logger.info(f"Frequency changed for channel {self.channel} from {self.frequency} to {frequency}")
        self.frequency = frequency

    def stop(self) -> None:
        """Stop PWM."""
        logger.info(f"Stop PWM on channel {self.channel} with duty cycle {self.dutycycle}")


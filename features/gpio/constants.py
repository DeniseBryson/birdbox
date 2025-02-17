"""
GPIO Hardware Constants
STABLE - Hardware interface with singleton pattern
"""
from collections.abc import Callable
import io
from typing import Literal, Final, TypeAlias

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
BOARD: Final = 10

# Update callback type to include both pin and state
EventCallback: TypeAlias = Callable[[int, PinState], None]

def is_raspberrypi():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception: pass
    return False

IS_RASPBERRYPI: Final[bool] = is_raspberrypi()
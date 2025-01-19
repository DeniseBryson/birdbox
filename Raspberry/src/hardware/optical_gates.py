import RPi.GPIO as GPIO
from ..utils.logger import setup_logger
from ..config.settings import PIN_CONFIG

logger = setup_logger()

class OpticalGates:
    def __init__(self):
        self.gate1_pin = PIN_CONFIG['OPTICAL_GATE_1_PIN']
        self.gate2_pin = PIN_CONFIG['OPTICAL_GATE_2_PIN']

        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gate1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.gate2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read_gates(self):
        gate1_state = GPIO.input(self.gate1_pin)
        gate2_state = GPIO.input(self.gate2_pin)
        logger.debug(f"Gate 1 state: {gate1_state}, Gate 2 state: {gate2_state}")
        return gate1_state, gate2_state

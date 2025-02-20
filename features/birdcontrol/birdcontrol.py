
import logging
from features.birdcontrol.motor_controller import MotorController
from features.birdcontrol.optical_gates import OpticalGates
from config.settings import PIN_CONFIG
import time

logger = logging.getLogger(__name__)

class BirdControl:
    """
    Manages the control of two motors by reading the state of the optical gates.
    """
    def __init__(self):
        self.motors = MotorController()
        self.start_pin = PIN_CONFIG['OPTICAL_GATE_1_PIN']
        self.end_pin = PIN_CONFIG['OPTICAL_GATE_2_PIN']
        
        def callback(pin: int, state: int) -> None:
            logger.debug(f"Gate {pin} state changed to {state}, RÜTTELN!!")
            if pin == self.start_pin:
                self.motors.turn_on()       
                time.sleep(5)
                self.motors.turn_off()
            elif pin == self.end_pin:
                self.motors.turn_off()

        self.optical_gates = OpticalGates(callback=callback)
        logger.info("System initialized and ready")
        
def main():
    """Initialize the bird control components"""
    try:
        BirdControl()
        while True:
            time.sleep(5)
            logger.info("System running")

    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
    finally:
        #motors.cleanup()
        #GPIO.cleanup()
        logger.info("GPIO cleanup completed")

if __name__ == "__main__":
    main()

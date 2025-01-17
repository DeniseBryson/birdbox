import time
try:
    import RPi.GPIO as GPIO # type: ignore
except ImportError:
    from fake_rpi import GPIO
from src.hardware.motor_controller import MotorController
from src.hardware.optical_gates import OpticalGates
from src.utils.logger import setup_logger
from src.config.settings import MOTOR_CONFIG

logger = setup_logger()

def main():
    try:
        motors = MotorController()
        gates = OpticalGates()
        current_freq = MOTOR_CONFIG['INITIAL_FREQUENCY']

        logger.info("System initialized and ready")

        while True:
            gate1_state, gate2_state = gates.read_gates()

            if not gate1_state:  # Gate 1 triggered
                logger.info("Optical gate 1 triggered - Starting motors")
                motors.turn_on()
                # Vary frequency
                current_freq = (current_freq % MOTOR_CONFIG['MAX_FREQUENCY']) + MOTOR_CONFIG['MIN_FREQUENCY']
                motors.set_frequency(current_freq)

            if not gate2_state:  # Gate 2 triggered
                logger.info("Optical gate 2 triggered - Stopping motors")
                motors.turn_off()

            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
    finally:
        motors.cleanup()
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")

if __name__ == "__main__":
    main()

from features.gpio.manager import gpio_manager as GPIOManager, OUT
from config.logging import logging
from config.settings import PIN_CONFIG, MOTOR_CONFIG

logger = logging.getLogger(__name__)

class MotorController:
    """
    Manages the control of two motors.
    """
    def __init__(self):
        self.motor1_pin = PIN_CONFIG['MOTOR_1_PIN']
        self.motor2_pin = PIN_CONFIG['MOTOR_2_PIN']
        self.current_freq = MOTOR_CONFIG['INITIAL_FREQUENCY']
        
        logger.info(f"Initial state: {GPIOManager.get_configured_pins()}")
        # Set pins as output
        logger.info(f"Configuring motor pins as output")
        GPIOManager.configure_pin(self.motor1_pin, OUT) #TODO: CALLBACKS
        GPIOManager.configure_pin(self.motor2_pin, OUT)
        
        # Set up PWM for both motors (try using hardware PWM with same generator)
        logger.info(f"Setting up PWM for both motors")
        GPIOManager.setup_pwm(self.motor1_pin, self.current_freq)
        GPIOManager.setup_pwm(self.motor2_pin, self.current_freq)

    def set_frequency(self, freq:int):
        """
        Set the frequency of the motors.
        """
        try:
            GPIOManager.set_pwm_frequency(self.motor1_pin, freq)
            GPIOManager.set_pwm_frequency(self.motor2_pin, freq)
            self.current_freq = freq
            logger.info(f"Motor frequency changed to {freq}Hz")
        except Exception as e:
            logger.error(f"Error changing frequency: {e}")

    def turn_on(self, duty_cycle:float=MOTOR_CONFIG['INITIAL_DUTY_CYCLE']):
        """
        Turn on the motors with a preset duty cycle.
        """
        try:
            GPIOManager.start_pwm(self.motor1_pin, duty_cycle)
            GPIOManager.start_pwm(self.motor2_pin, duty_cycle)
            logger.info(f"Motors turned ON with {duty_cycle}% duty cycle")
        except Exception as e:
            logger.error(f"Error turning motors on: {e}")

    def turn_off(self):
        """
        Turn off the motors.
        """
        try:
            GPIOManager.stop_pwm(self.motor1_pin)
            GPIOManager.stop_pwm(self.motor2_pin)
            logger.info("Motors turned OFF")
        except Exception as e:
            logger.error(f"Error turning motors off: {e}")

    def cleanup(self):
        """
        Clean up the motors.
        """
        self.turn_off()
        GPIOManager.remove_pwm(self.motor1_pin)
        GPIOManager.remove_pwm(self.motor2_pin)


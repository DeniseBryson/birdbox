import RPi.GPIO as GPIO
from ..utils.logger import setup_logger
from ..config.settings import PIN_CONFIG, MOTOR_CONFIG

logger = setup_logger()

class MotorController:
    def __init__(self):
        self.motor1_pin = PIN_CONFIG['MOTOR_1_PIN']
        self.motor2_pin = PIN_CONFIG['MOTOR_2_PIN']
        self.current_freq = MOTOR_CONFIG['INITIAL_FREQUENCY']

        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.motor1_pin, GPIO.OUT)
        GPIO.setup(self.motor2_pin, GPIO.OUT)

        # Set up PWM
        self.motor1_pwm = GPIO.PWM(self.motor1_pin, self.current_freq)
        self.motor2_pwm = GPIO.PWM(self.motor2_pin, self.current_freq)
        self.motor1_pwm.start(0)
        self.motor2_pwm.start(0)

    def set_frequency(self, freq):
        try:
            self.motor1_pwm.ChangeFrequency(freq)
            self.motor2_pwm.ChangeFrequency(freq)
            self.current_freq = freq
            logger.info(f"Motor frequency changed to {freq}Hz")
        except Exception as e:
            logger.error(f"Error changing frequency: {e}")

    def turn_on(self, duty_cycle=MOTOR_CONFIG['INITIAL_DUTY_CYCLE']):
        try:
            self.motor1_pwm.ChangeDutyCycle(duty_cycle)
            self.motor2_pwm.ChangeDutyCycle(duty_cycle)
            logger.info(f"Motors turned ON with {duty_cycle}% duty cycle")
        except Exception as e:
            logger.error(f"Error turning motors on: {e}")

    def turn_off(self):
        try:
            self.motor1_pwm.ChangeDutyCycle(0)
            self.motor2_pwm.ChangeDutyCycle(0)
            logger.info("Motors turned OFF")
        except Exception as e:
            logger.error(f"Error turning motors off: {e}")

    def cleanup(self):
        self.turn_off()
        self.motor1_pwm.stop()
        self.motor2_pwm.stop()

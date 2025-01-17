try:
    import RPi.GPIO as GPIO
except ImportError:
    from fake_rpi import GPIO
import time

def run_vibrator():
    # Use GPIO BCM numbering
    GPIO.setmode(GPIO.BCM)

    # Define the vibrator motor pin (GPIO 18 is commonly used)
    MOTOR_PIN = 18  # Connected to 3.3V compatible vibration motor

    # Setup the motor pin as output
    GPIO.setup(MOTOR_PIN, GPIO.OUT)

    try:
        while True:
            # Turn motor on
            print("Vibrator ON")
            GPIO.output(MOTOR_PIN, GPIO.HIGH)
            time.sleep(1)

            # Turn motor off
            print("Vibrator OFF")
            GPIO.output(MOTOR_PIN, GPIO.LOW)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram stopped by user")
        GPIO.cleanup()

if __name__ == "__main__":
    run_vibrator()

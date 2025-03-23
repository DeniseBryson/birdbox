import RPi.GPIO as RPI_GPIO
from features.gpio import GPIOManager
import time

from features.gpio.hardware import OUT

def print_separator():
    print("\n" + "="*50 + "\n")

# 1. Direct RPI.GPIO test first
print_separator()
print("=== Direct RPi.GPIO Test ===")
RPI_GPIO.setmode(RPI_GPIO.BCM)
RPI_GPIO.setwarnings(False)

PIN = 18

print("Setting up pin directly with RPi.GPIO...")
RPI_GPIO.setup(PIN, RPI_GPIO.OUT)
print(f"Pin {PIN} function:", RPI_GPIO.gpio_function(PIN))

print("\nBlinking with direct RPi.GPIO...")
for _ in range(3):
    print("HIGH")
    RPI_GPIO.output(PIN, RPI_GPIO.HIGH)
    time.sleep(1)
    print("LOW")
    RPI_GPIO.output(PIN, RPI_GPIO.LOW)
    time.sleep(1)

RPI_GPIO.cleanup()

# 2. GPIOManager test
print_separator()
print("=== GPIOManager Test ===")
gpio = GPIOManager()

print("\nTesting hardware detection:")
print(f"Is Raspberry Pi: {gpio.is_raspberry_pi}")

print("\nInitial state:")
try:
    state = gpio.get_pin_state(PIN)
    print(f"Pin {PIN} state:", state)
except Exception as e:
    print(f"Error getting state: {e}")

print("\nConfiguring pin...")
state = gpio.configure_pin(PIN, OUT)
print(f"After configure state: {state}")
print(f"Direct GPIO function check: {RPI_GPIO.gpio_function(PIN)}")

print("\nBlinking with GPIOManager...")
for _ in range(3):
    print("\nCycle", _ + 1)
    print("Setting HIGH")
    state = gpio.set_pin_state(PIN, 1)
    print(f"State after HIGH: {state}")
    print(f"Direct GPIO read: {RPI_GPIO.input(PIN)}")
    time.sleep(1)
    
    print("Setting LOW")
    state = gpio.set_pin_state(PIN, 0)
    print(f"State after LOW: {state}")
    print(f"Direct GPIO read: {RPI_GPIO.input(PIN)}")
    time.sleep(1)

gpio.cleanup()

# 3. Rapid switching test
print_separator()
print("=== Rapid Switching Test ===")
gpio = GPIOManager()
gpio.configure_pin(PIN, OUT)

print("Rapid switching 10 times...")
for i in range(10):
    gpio.set_pin_state(PIN, 1)
    direct_read_high = RPI_GPIO.input(PIN)
    gpio.set_pin_state(PIN, 0)
    direct_read_low = RPI_GPIO.input(PIN)
    print(f"Cycle {i+1}: HIGH read: {direct_read_high}, LOW read: {direct_read_low}")

gpio.cleanup()
print_separator()
print("Debug complete!") 
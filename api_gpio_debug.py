import requests
import time
import json
import RPi.GPIO as RPI_GPIO

BASE_URL = "http://localhost:8080"

def verify_gpio_state(pin, expected_state):
    """Verify the actual GPIO state matches expected state."""
    try:
        actual_state = RPI_GPIO.input(pin)
        print(f"Direct GPIO Read - Expected: {expected_state}, Actual: {actual_state}")
        return actual_state == expected_state
    except Exception as e:
        print(f"Error reading GPIO: {e}")
        return False

def setup_gpio(pin):
    """Set up GPIO pin for testing."""
    try:
        RPI_GPIO.setup(pin, RPI_GPIO.OUT)
        print(f"GPIO pin {pin} set up as output")
        return True
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        return False

def print_separator():
    print("\n" + "="*50 + "\n")

def test_api():
    PIN = 18
    
    # Set up GPIO mode
    print("Setting up GPIO...")
    RPI_GPIO.setmode(RPI_GPIO.BCM)
    RPI_GPIO.setwarnings(False)
    setup_gpio(PIN)
    
    print_separator()
    print("=== Testing GPIO API ===")
    
    # 1. Get initial pin states
    print("\n1. Getting initial pin states...")
    response = requests.get(f"{BASE_URL}/gpio/api/pins")
    print("Response:", json.dumps(response.json(), indent=2))
    
    # 2. Configure pin as output
    print("\n2. Configuring pin as output...")
    response = requests.post(
        f"{BASE_URL}/gpio/api/configure",
        json={"pin": PIN, "mode": "OUT"}
    )
    print("Response:", json.dumps(response.json(), indent=2))
    
    # Verify configuration
    print("\nVerifying configuration directly...")
    func = RPI_GPIO.gpio_function(PIN)
    print(f"GPIO function: {func} (should be 1 for output)")
    
    # 3. Get pin states after configuration
    print("\n3. Getting pin states after configuration...")
    response = requests.get(f"{BASE_URL}/gpio/api/pins")
    print("Response:", json.dumps(response.json(), indent=2))
    
    # 4. Test setting pin HIGH and LOW
    print("\n4. Testing pin state changes...")
    for i in range(3):
        print(f"\nCycle {i+1}")
        
        # Set HIGH
        print("Setting HIGH...")
        response = requests.post(
            f"{BASE_URL}/gpio/api/state",
            json={"pin": PIN, "state": 1}
        )
        print("HIGH Response:", json.dumps(response.json(), indent=2))
        
        # Verify state through API
        response = requests.get(f"{BASE_URL}/gpio/api/pins")
        pin_state = next((p for p in response.json()['pins'] if p['number'] == PIN), None)
        print(f"API reported state: {pin_state}")
        
        # Verify state directly
        print("Direct GPIO verification:")
        verify_gpio_state(PIN, 1)
        
        time.sleep(1)
        
        # Set LOW
        print("Setting LOW...")
        response = requests.post(
            f"{BASE_URL}/gpio/api/state",
            json={"pin": PIN, "state": 0}
        )
        print("LOW Response:", json.dumps(response.json(), indent=2))
        
        # Verify state through API
        response = requests.get(f"{BASE_URL}/gpio/api/pins")
        pin_state = next((p for p in response.json()['pins'] if p['number'] == PIN), None)
        print(f"API reported state: {pin_state}")
        
        # Verify state directly
        print("Direct GPIO verification:")
        verify_gpio_state(PIN, 0)
        
        time.sleep(1)
    
    # Cleanup
    print("\nCleaning up GPIO...")
    RPI_GPIO.cleanup()
    
    print_separator()
    print("API test complete!")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"Test failed: {e}")
        RPI_GPIO.cleanup()  # Ensure cleanup on error 
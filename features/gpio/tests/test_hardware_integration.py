"""
Hardware Integration Tests for GPIO Manager
These tests will only run on actual Raspberry Pi hardware
"""
import pytest
import platform
import RPi.GPIO as RPI_GPIO
from ..manager import GPIOManager
import os

def is_raspberry_pi():
    """Check if we're running on a Raspberry Pi."""
    # Check for Raspberry Pi model file
    is_pi = os.path.exists('/sys/firmware/devicetree/base/model')
    if is_pi:
        with open('/sys/firmware/devicetree/base/model') as f:
            model = f.read()
            is_pi = model.startswith('Raspberry Pi')
    
    return is_pi and RPI_GPIO is not None

# Skip all tests if not on Raspberry Pi
pytestmark = pytest.mark.skipif(not is_raspberry_pi(), 
                              reason="Hardware tests only run on Raspberry Pi")

@pytest.fixture(scope="function")
def hw_gpio():
    """Fixture for hardware GPIO testing."""
    RPI_GPIO.setwarnings(False)  # Disable warnings for all tests
    manager = GPIOManager()
    yield manager
    manager.cleanup()
    RPI_GPIO.cleanup()  # Ensure complete cleanup after each test

def test_hardware_detection(hw_gpio):
    """Test that we're correctly detecting Raspberry Pi hardware."""
    # Debug information
    print(f"\nPlatform: {platform.machine()}")
    print(f"Model file exists: {os.path.exists('/sys/firmware/devicetree/base/model')}")
    if os.path.exists('/sys/firmware/devicetree/base/model'):
        with open('/sys/firmware/devicetree/base/model') as f:
            print(f"Model: {f.read()}")
    print(f"RPi.GPIO available: {RPI_GPIO is not None}")
    
    assert hw_gpio.is_raspberry_pi, "Should detect real Raspberry Pi hardware"

def test_output_functionality(hw_gpio):
    """Test basic output functionality on real hardware."""
    PIN = 18  # This is a safe pin to test with
    
    # Configure as output
    state = hw_gpio.configure_pin(PIN, "OUT")
    assert state['mode'] == "OUT"
    assert state['pin'] == PIN
    
    # Set HIGH
    state = hw_gpio.set_pin_state(PIN, 1)
    assert state['state'] == 1
    
    # Verify actual hardware state
    assert RPI_GPIO.input(PIN) == 1
    
    # Set LOW
    state = hw_gpio.set_pin_state(PIN, 0)
    assert state['state'] == 0
    
    # Verify actual hardware state
    assert RPI_GPIO.input(PIN) == 0

def test_input_functionality(hw_gpio):
    """Test input functionality on real hardware."""
    PIN = 24  # Using a different pin for input
    
    # Configure as input
    state = hw_gpio.configure_pin(PIN, "IN")
    assert state['mode'] == "IN"
    assert state['pin'] == PIN
    
    # Read state
    state = hw_gpio.get_pin_state(PIN)
    assert 'state' in state
    assert state['pin'] == PIN

def test_multiple_pins(hw_gpio):
    """Test handling multiple pins simultaneously."""
    OUTPUT_PIN = 18
    INPUT_PIN = 23
    
    # Configure pins
    out_state = hw_gpio.configure_pin(OUTPUT_PIN, "OUT")
    in_state = hw_gpio.configure_pin(INPUT_PIN, "IN")
    
    assert out_state['mode'] == "OUT"
    assert in_state['mode'] == "IN"
    
    # Test output pin
    hw_gpio.set_pin_state(OUTPUT_PIN, 1)
    assert hw_gpio.get_pin_state(OUTPUT_PIN)['state'] == 1
    
    hw_gpio.set_pin_state(OUTPUT_PIN, 0)
    assert hw_gpio.get_pin_state(OUTPUT_PIN)['state'] == 0
    
    # Input pin should maintain its state
    assert hw_gpio.get_pin_state(INPUT_PIN)['mode'] == "IN" 
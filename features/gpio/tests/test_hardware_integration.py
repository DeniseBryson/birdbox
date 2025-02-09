"""
Hardware Integration Tests for GPIO Manager
These tests will only run on actual Raspberry Pi hardware
"""
import pytest
import platform
import os

# Try to import RPi.GPIO, but don't fail if not available
try:
    import RPi.GPIO as RPI_GPIO
except ImportError:
    RPI_GPIO = None

from ..manager import GPIOManager, HW

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
    
    # Reset singleton state
    GPIOManager._instance = None
    GPIOManager._initialized = False
    
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
    hw_gpio.configure_pin(PIN, HW.OUT)
    configured_pins = hw_gpio.get_configured_pins()
    assert PIN in configured_pins
    assert configured_pins[PIN] == HW.OUT
    
    # Set HIGH
    hw_gpio.set_pin_state(PIN, HW.HIGH)
    assert hw_gpio.get_pin_state(PIN) == HW.HIGH
    
    # Verify actual hardware state
    assert RPI_GPIO.input(PIN) == HW.HIGH
    
    # Set LOW
    hw_gpio.set_pin_state(PIN, HW.LOW)
    assert hw_gpio.get_pin_state(PIN) == HW.LOW
    
    # Verify actual hardware state
    assert RPI_GPIO.input(PIN) == HW.LOW

def test_input_functionality(hw_gpio):
    """Test input functionality on real hardware."""
    PIN = 24  # Using a different pin for input
    
    # Configure as input
    hw_gpio.configure_pin(PIN, HW.IN)
    configured_pins = hw_gpio.get_configured_pins()
    assert PIN in configured_pins
    assert configured_pins[PIN] == HW.IN
    
    # Read state (should be either HIGH or LOW)
    state = hw_gpio.get_pin_state(PIN)
    assert state in [HW.HIGH, HW.LOW]

def test_multiple_pins(hw_gpio):
    """Test handling multiple pins simultaneously."""
    OUTPUT_PIN = 18
    INPUT_PIN = 23
    
    # Configure pins
    hw_gpio.configure_pin(OUTPUT_PIN, HW.OUT)
    hw_gpio.configure_pin(INPUT_PIN, HW.IN)
    
    configured_pins = hw_gpio.get_configured_pins()
    assert OUTPUT_PIN in configured_pins
    assert INPUT_PIN in configured_pins
    assert configured_pins[OUTPUT_PIN] == HW.OUT
    assert configured_pins[INPUT_PIN] == HW.IN
    
    # Test output pin
    hw_gpio.set_pin_state(OUTPUT_PIN, HW.HIGH)
    assert hw_gpio.get_pin_state(OUTPUT_PIN) == HW.HIGH
    
    hw_gpio.set_pin_state(OUTPUT_PIN, HW.LOW)
    assert hw_gpio.get_pin_state(OUTPUT_PIN) == HW.LOW
    
    # Input pin should maintain its mode
    assert configured_pins[INPUT_PIN] == HW.IN 
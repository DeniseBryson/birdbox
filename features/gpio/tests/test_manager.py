"""
Tests for GPIO Manager functionality
"""
import pytest
import platform
import os

# Try to import RPi.GPIO, but don't fail if not available
try:
    import RPi.GPIO as RPI_GPIO
except ImportError:
    RPI_GPIO = None

from ..manager import GPIOManager, GPIO

def is_raspberry_pi():
    """Check if we're running on a real Raspberry Pi."""
    try:
        with open('/sys/firmware/devicetree/base/model') as f:
            print('We are running the test on a Raspberry Pi')
            return 'Raspberry Pi' in f.read() and RPI_GPIO is not None
    except:
        print('We are running the test in a mock environment')
        return False

@pytest.fixture
def gpio_manager():
    """Fixture providing a GPIO manager instance."""
    if is_raspberry_pi():
        # Set up GPIO mode for real hardware
        RPI_GPIO.setmode(RPI_GPIO.BCM)
        RPI_GPIO.setwarnings(False)
    
    # Reset the singleton state before each test
    GPIOManager._instance = None
    GPIOManager._initialized = False
    
    manager = GPIOManager()
    yield manager
    
    # Proper cleanup
    manager.cleanup()
    if is_raspberry_pi():
        RPI_GPIO.cleanup()

def test_gpio_initialization(gpio_manager):
    """Test GPIO manager initializes correctly."""
    assert gpio_manager.is_raspberry_pi == is_raspberry_pi()
    if not gpio_manager.is_raspberry_pi:
        assert isinstance(gpio_manager._mock_states, dict)
        assert len(gpio_manager._mock_states) == len(gpio_manager.get_available_pins())

def test_available_pins(gpio_manager):
    """Test getting available GPIO pins."""
    pins = gpio_manager.get_available_pins()
    assert isinstance(pins, list)
    assert len(pins) > 0
    assert all(isinstance(pin, int) for pin in pins)

def test_pin_state(gpio_manager):
    """Test getting pin state."""
    pin = gpio_manager.get_available_pins()[0]
    
    # Configure pin first
    gpio_manager.configure_pin(pin, GPIO.IN)
    state = gpio_manager.get_pin_state(pin)
    
    # These checks work for both real and mock GPIO
    assert isinstance(state, int)
    assert state in [GPIO.LOW, GPIO.HIGH]
    
    # Test invalid pin
    with pytest.raises(ValueError):
        gpio_manager.get_pin_state(999)
        
    # Test unconfigured pin
    unconfigured_pin = gpio_manager.get_available_pins()[-1]
    with pytest.raises(RuntimeError):
        gpio_manager.get_pin_state(unconfigured_pin)

def test_configure_pin(gpio_manager):
    """Test configuring pin mode."""
    pin = gpio_manager.get_available_pins()[0]
    
    # Test setting as input
    gpio_manager.configure_pin(pin, GPIO.IN)
    configured_pins = gpio_manager.get_configured_pins()
    assert pin in configured_pins
    assert configured_pins[pin] == GPIO.IN
    
    # Test setting as output
    gpio_manager.configure_pin(pin, GPIO.OUT)
    configured_pins = gpio_manager.get_configured_pins()
    assert pin in configured_pins
    assert configured_pins[pin] == GPIO.OUT
    
    # Test invalid mode
    with pytest.raises(ValueError):
        gpio_manager.configure_pin(pin, 'INVALID')
        
    # Test invalid pin
    with pytest.raises(ValueError):
        gpio_manager.configure_pin(999, GPIO.IN)

    # Test callback functionality
    callback_called = False
    def test_callback(channel):
        nonlocal callback_called
        callback_called = True
    
    # Configure input pin with callback
    gpio_manager.configure_pin(pin, GPIO.IN, callback=test_callback)
    
    # Simulate pin change (for mock GPIO)
    if not gpio_manager.is_raspberry_pi:
        gpio_manager._mock_states[pin]['state'] = GPIO.HIGH
        if 'callback' in gpio_manager._mock_states[pin]:
            gpio_manager._mock_states[pin]['callback'](pin)
        
    assert callback_called, "Callback was not triggered"
    
    # Test removing callback
    callback_called = False
    gpio_manager.configure_pin(pin, GPIO.IN, callback=None)
    
    # Simulate pin change again
    if not gpio_manager.is_raspberry_pi:
        gpio_manager._mock_states[pin]['state'] = GPIO.LOW
        if 'callback' in gpio_manager._mock_states[pin]:
            gpio_manager._mock_states[pin]['callback'](pin)
            
    assert not callback_called, "Callback was triggered after removal"

    
@pytest.mark.skipif(is_raspberry_pi(), reason="Mock-specific test")
def test_set_pin_state_mock(gpio_manager):
    """Test setting pin state in mock environment."""
    pin = gpio_manager.get_available_pins()[0]
    unconfigured_pin = gpio_manager.get_available_pins()[-1]
    input_pin = gpio_manager.get_available_pins()[1]
    
    # Test setting state on unconfigured pin
    with pytest.raises(RuntimeError):
        gpio_manager.set_pin_state(unconfigured_pin, GPIO.HIGH)
    
    # Configure pins
    gpio_manager.configure_pin(pin, GPIO.OUT)
    gpio_manager.configure_pin(input_pin, GPIO.IN)
    
    # Test setting HIGH
    gpio_manager.set_pin_state(pin, GPIO.HIGH)
    assert gpio_manager.get_pin_state(pin) == GPIO.HIGH
    
    # Test setting LOW
    gpio_manager.set_pin_state(pin, GPIO.LOW)
    assert gpio_manager.get_pin_state(pin) == GPIO.LOW
    
    # Test invalid state
    with pytest.raises(ValueError):
        gpio_manager.set_pin_state(pin, 2)
    
    # Test setting state on input pin
    with pytest.raises(ValueError):
        gpio_manager.set_pin_state(input_pin, GPIO.HIGH)

@pytest.mark.skipif(is_raspberry_pi(), reason="Mock-specific test")
def test_cleanup_mock(gpio_manager):
    """Test GPIO cleanup in mock environment."""
    test_pins = gpio_manager.get_available_pins()[:2]
    
    gpio_manager.configure_pin(test_pins[0], GPIO.OUT)
    gpio_manager.configure_pin(test_pins[1], GPIO.IN)
    gpio_manager.set_pin_state(test_pins[0], GPIO.HIGH)
    
    # Verify mock states
    assert gpio_manager._mock_states[test_pins[0]]['mode'] == GPIO.OUT
    assert gpio_manager._mock_states[test_pins[0]]['state'] == GPIO.HIGH
    assert gpio_manager._mock_states[test_pins[1]]['mode'] == GPIO.IN
    
    gpio_manager.cleanup()
    
    # Verify reset states
    for pin in test_pins:
        assert gpio_manager._mock_states[pin]['mode'] == GPIO.IN
        assert gpio_manager._mock_states[pin]['state'] == GPIO.LOW
        assert not gpio_manager._mock_states[pin]['configured']

@pytest.mark.skipif(not is_raspberry_pi(), reason="Hardware tests only run on Raspberry Pi")
def test_hardware_specific(gpio_manager):
    """Test features specific to real hardware."""
    assert gpio_manager.is_raspberry_pi
    pin = 18  # Common GPIO pin for testing
    
    # Set up pin
    gpio_manager.configure_pin(pin, GPIO.OUT)
    
    # Test HIGH
    gpio_manager.set_pin_state(pin, GPIO.HIGH)
    assert gpio_manager.get_pin_state(pin) == GPIO.HIGH
    
    # Test LOW
    gpio_manager.set_pin_state(pin, GPIO.LOW)
    assert gpio_manager.get_pin_state(pin) == GPIO.LOW

@pytest.mark.skipif(not is_raspberry_pi(), reason="Hardware tests only run on Raspberry Pi")
def test_hardware_cleanup(gpio_manager):
    """Test cleanup on real hardware."""
    pin = 18
    
    # Configure and set pin
    gpio_manager.configure_pin(pin, GPIO.OUT)
    gpio_manager.set_pin_state(pin, GPIO.HIGH)
    
    # Verify state
    assert gpio_manager.get_pin_state(pin) == GPIO.HIGH
    
    # Cleanup
    gpio_manager.cleanup()
    
    # Should be able to configure pin again
    gpio_manager.configure_pin(pin, GPIO.OUT)
    assert gpio_manager.get_pin_state(pin) == GPIO.LOW 
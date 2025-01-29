"""
Tests for GPIO Manager functionality
"""
import pytest
import platform
import RPi.GPIO as RPI_GPIO
from ..manager import GPIOManager

def is_raspberry_pi():
    """Check if we're running on a real Raspberry Pi."""
    try:
        with open('/sys/firmware/devicetree/base/model') as f:
            print('We are running the test on a Raspberry Pi')
            return 'Raspberry Pi' in f.read()
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
    gpio_manager.configure_pin(pin, 'IN')
    state = gpio_manager.get_pin_state(pin)
    
    # These checks work for both real and mock GPIO
    assert isinstance(state, dict)
    assert 'pin' in state
    assert 'mode' in state
    assert 'state' in state
    assert 'name' in state
    assert state['mode'] == 'IN'
    
    with pytest.raises(ValueError):
        gpio_manager.get_pin_state(999)

def test_configure_pin(gpio_manager):
    """Test configuring pin mode."""
    pin = gpio_manager.get_available_pins()[0]
    
    # Test setting as input
    state = gpio_manager.configure_pin(pin, 'IN')
    assert state['mode'] == 'IN'
    
    # Test setting as output
    state = gpio_manager.configure_pin(pin, 'OUT')
    assert state['mode'] == 'OUT'
    
    # Test invalid mode
    with pytest.raises(ValueError):
        gpio_manager.configure_pin(pin, 'INVALID')
        
    # Test invalid pin
    with pytest.raises(ValueError):
        gpio_manager.configure_pin(999, 'IN')

@pytest.mark.skipif(is_raspberry_pi(), reason="Mock-specific test")
def test_set_pin_state_mock(gpio_manager):
    """Test setting pin state in mock environment."""
    pin = gpio_manager.get_available_pins()[0]
    
    # Configure as output first
    gpio_manager.configure_pin(pin, 'OUT')
    
    # Test setting HIGH
    state = gpio_manager.set_pin_state(pin, 1)
    assert state['state'] == 1
    
    # Test setting LOW
    state = gpio_manager.set_pin_state(pin, 0)
    assert state['state'] == 0
    
    # Test invalid state
    with pytest.raises(ValueError):
        gpio_manager.set_pin_state(pin, 2)
    
    # Test setting state on input pin
    input_pin = gpio_manager.get_available_pins()[1]
    gpio_manager.configure_pin(input_pin, 'IN')
    with pytest.raises(ValueError):
        gpio_manager.set_pin_state(input_pin, 1)

@pytest.mark.skipif(is_raspberry_pi(), reason="Mock-specific test")
def test_cleanup_mock(gpio_manager):
    """Test GPIO cleanup in mock environment."""
    test_pins = gpio_manager.get_available_pins()[:2]
    
    gpio_manager.configure_pin(test_pins[0], 'OUT')
    gpio_manager.configure_pin(test_pins[1], 'IN')
    gpio_manager.set_pin_state(test_pins[0], 1)
    
    # Verify mock states
    assert gpio_manager._mock_states[test_pins[0]]['mode'] == 'OUT'
    assert gpio_manager._mock_states[test_pins[0]]['state'] == 1
    assert gpio_manager._mock_states[test_pins[1]]['mode'] == 'IN'
    
    gpio_manager.cleanup()
    
    # Verify reset states
    for pin in test_pins:
        assert gpio_manager._mock_states[pin]['mode'] == 'IN'
        assert gpio_manager._mock_states[pin]['state'] == 0

@pytest.mark.skipif(not is_raspberry_pi(), reason="Hardware tests only run on Raspberry Pi")
def test_hardware_specific(gpio_manager):
    """Test features specific to real hardware."""
    assert gpio_manager.is_raspberry_pi
    pin = 18  # Common GPIO pin for testing
    
    # Set up pin
    gpio_manager.configure_pin(pin, 'OUT')
    
    # Test HIGH
    gpio_manager.set_pin_state(pin, 1)
    state = gpio_manager.get_pin_state(pin)
    assert state['state'] == 1
    
    # Test LOW
    gpio_manager.set_pin_state(pin, 0)
    state = gpio_manager.get_pin_state(pin)
    assert state['state'] == 0

@pytest.mark.skipif(not is_raspberry_pi(), reason="Hardware tests only run on Raspberry Pi")
def test_hardware_cleanup(gpio_manager):
    """Test cleanup on real hardware."""
    pin = 18
    
    # Configure and set pin
    gpio_manager.configure_pin(pin, 'OUT')
    gpio_manager.set_pin_state(pin, 1)
    
    # Verify state
    state = gpio_manager.get_pin_state(pin)
    assert state['state'] == 1
    
    # Cleanup
    gpio_manager.cleanup()
    
    # Should be able to configure pin again
    gpio_manager.configure_pin(pin, 'OUT')
    state = gpio_manager.get_pin_state(pin)
    assert state['mode'] == 'OUT' 
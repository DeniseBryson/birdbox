"""
Tests for GPIO Manager functionality
"""
import pytest
from ..manager import GPIOManager

@pytest.fixture
def gpio_manager():
    """Fixture providing a GPIO manager instance."""
    manager = GPIOManager()
    yield manager
    manager.cleanup()

def test_gpio_initialization(gpio_manager):
    """Test GPIO manager initializes correctly."""
    assert not gpio_manager.is_raspberry_pi  # Should be False in test environment
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
    state = gpio_manager.get_pin_state(pin)
    
    assert isinstance(state, dict)
    assert 'pin' in state
    assert 'mode' in state
    assert 'state' in state
    assert 'name' in state
    
    with pytest.raises(ValueError):
        gpio_manager.get_pin_state(999)  # Invalid pin

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

def test_set_pin_state(gpio_manager):
    """Test setting pin state."""
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

def test_cleanup(gpio_manager):
    """Test GPIO cleanup."""
    # Configure some pins
    pins = gpio_manager.get_available_pins()[:2]
    gpio_manager.configure_pin(pins[0], 'OUT')
    gpio_manager.configure_pin(pins[1], 'IN')
    gpio_manager.set_pin_state(pins[0], 1)
    
    # Cleanup
    gpio_manager.cleanup()
    
    # Verify all pins are reset to default state
    for pin in gpio_manager.get_available_pins():
        state = gpio_manager._mock_states[pin]
        assert state['mode'] == 'IN'
        assert state['state'] == 0
        assert state['configured'] == False 
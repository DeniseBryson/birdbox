# pyright: reportPrivateUsage=false
"""
Test suite for GPIO Manager
"""
import pytest
from unittest.mock import Mock, patch
from features.gpio.hardware import (
    HIGH, LOW, IN, OUT, PUD_OFF, UNDEFINED
)
from features.gpio.manager import GPIOManager

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton instance before each test"""
    GPIOManager._instance = None
    GPIOManager._initialized = False
    yield

@pytest.fixture
def mock_hardware():
    """Mock the hardware interface"""
    with patch('features.gpio.manager.HW') as mock:
        # Set up common GPIO constants on the mock
        mock.IN = IN
        mock.OUT = OUT
        mock.HIGH = HIGH
        mock.LOW = LOW
        mock.PUD_OFF = PUD_OFF
        mock.UNDEFINED = UNDEFINED
        yield mock

@pytest.fixture
def gpio_manager(mock_hardware: Mock):
    """Creates a GPIOManager instance with mocked hardware"""
    manager = GPIOManager()
    return manager

@pytest.fixture
def mock_logger():
    with patch('features.gpio.manager.logger') as mock:
        yield mock

class TestGPIOManager:
    
    def test_singleton_pattern(self, gpio_manager: GPIOManager):
        """Test that GPIOManager implements singleton pattern correctly"""
        manager1 = GPIOManager()
        manager2 = GPIOManager()
        assert manager1 is manager2
        assert manager1 is gpio_manager
    
    def test_get_available_pins(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test getting available pins delegates to hardware"""
            # Reset the mock to clear the initialization call
        mock_hardware.get_valid_pins.reset_mock()
        
        mock_hardware.get_valid_pins.return_value = [2, 3, 4]
        pins = gpio_manager.valid_pins
        assert pins == [2, 3, 4]
        mock_hardware.get_valid_pins.assert_called_once()

    def test_configure_input_pin(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test configuring a pin as input"""
        pin = 18
        callback = Mock()
        
        gpio_manager.configure_pin(pin, IN, callback)
        
        # Verify hardware calls
        mock_hardware.setup_input_pin.assert_called_once_with(
            pin,
            edge_detection=True,
            callback=callback
        )
        
        # Verify internal state
        assert gpio_manager._pin_modes[pin] == IN
        assert pin not in gpio_manager._output_pin_states
        assert pin not in gpio_manager._output_pin_callbacks

    def test_configure_output_pin(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test configuring a pin as output"""
        pin = 18
        callback = Mock()
        
        gpio_manager.configure_pin(pin, OUT, callback)
        
        # Verify hardware calls
        mock_hardware.setup_output_pin.assert_called_once_with(
            pin,
            initial_state=HIGH
        )
        
        # Verify internal state
        assert gpio_manager._pin_modes[pin] == OUT
        assert gpio_manager._output_pin_states[pin] == HIGH
        assert gpio_manager._output_pin_callbacks[pin] == callback
        
        # Verify callback was triggered with initial state
        callback.assert_called_once_with(pin, HIGH)

    def test_get_pin_state_input_pin(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test getting state of an input pin"""
        mock_hardware.get_valid_pins.reset_mock()
        pin = 18
        gpio_manager._pin_modes[pin] = IN
        mock_hardware.get_valid_pins.return_value = [pin]
        mock_hardware.get_pin_state.return_value = HIGH
        
        state = gpio_manager.get_pin_state(pin)
        assert state == HIGH
        mock_hardware.get_valid_pins.assert_called_once_with()
        mock_hardware.get_pin_state.assert_called_once_with(pin)
   
    def test_get_pin_state_output_pin(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test getting state of an output pin"""
        mock_hardware.get_valid_pins.reset_mock()
        
        pin = 18
        mock_hardware.get_valid_pins.return_value = [pin]
        gpio_manager._pin_modes[pin] = OUT
        gpio_manager._output_pin_states[pin] = LOW
        
        state = gpio_manager.get_pin_state(pin)
        assert state == LOW
        mock_hardware.get_pin_state.assert_not_called()
        mock_hardware.get_valid_pins.assert_called_once_with()

    def test_get_pin_state_unconfigured(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test getting state of an unconfigured pin"""
        pin = 18
        mock_hardware.get_valid_pins.return_value = [pin]
        
        state = gpio_manager.get_pin_state(pin)
        assert state == UNDEFINED

    def test_get_pin_state_invalid_pin(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test getting state of an invalid pin"""
        pin = 999
        mock_hardware.get_valid_pins.return_value = [18]
        
        state = gpio_manager.get_pin_state(pin)
        assert state == UNDEFINED

    def test_set_pin_state(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test setting pin state"""
        pin = 18
        gpio_manager._pin_modes[pin] = OUT
        callback = Mock()
        gpio_manager._output_pin_callbacks[pin] = callback 
        
        gpio_manager.set_pin_state(pin, HIGH)
        
        # Verify hardware call
        mock_hardware.set_output_state.assert_called_once_with(pin, HIGH)
        
        # Verify internal state updated
        assert gpio_manager._output_pin_states[pin] == HIGH
        
        # Verify callback triggered
        callback.assert_called_once_with(pin, HIGH)

    def test_set_pin_state_input_pin(self, gpio_manager: GPIOManager):
        """Test setting state of an input pin fails"""
        pin = 18
        gpio_manager._pin_modes[pin] = IN
        
        with pytest.raises(ValueError, match="not configured as output"):
            gpio_manager.set_pin_state(pin, HIGH)

    def test_set_pin_state_unconfigured(self, gpio_manager: GPIOManager):
        """Test setting state of an unconfigured pin fails"""
        pin = 18
        
        with pytest.raises(RuntimeError, match="not configured"):
            gpio_manager.set_pin_state(pin, HIGH)

    def test_cleanup(self, gpio_manager: GPIOManager, mock_hardware: Mock):
        """Test cleanup"""
        # Setup some state
        pin = 18
        gpio_manager._pin_modes[pin] = OUT
        gpio_manager._output_pin_states[pin] = HIGH
        gpio_manager._output_pin_callbacks[pin] = Mock()
        
        gpio_manager.cleanup()
        
        # Verify hardware cleanup
        mock_hardware.cleanup.assert_called_once()
        
        # Verify internal state cleared
        assert not gpio_manager._pin_modes
        assert not gpio_manager._output_pin_states
        assert not gpio_manager._output_pin_callbacks 
# pyright: reportPrivateUsage=false
"""
Test suite for GPIO hardware interface
STABLE - Core hardware interface tests
"""
import pytest
from unittest.mock import Mock, patch
from features.gpio.hardware import (
    GPIOHardware, HIGH, LOW, IN, OUT, 
    PUD_OFF, PUD_UP, PUD_DOWN, BOTH, BCM
)

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton instance before each test"""
    GPIOHardware._instance = None
    GPIOHardware._initialized = False
    yield

@pytest.fixture
def mock_gpio():
    """Create a fresh mock of RPI_GPIO for each test"""
    with patch('features.gpio.hardware.RPI_GPIO') as mock:
        # Set up common GPIO constants on the mock
        mock.IN = IN
        mock.OUT = OUT
        mock.HIGH = HIGH
        mock.LOW = LOW
        mock.PUD_UP = PUD_UP
        mock.PUD_DOWN = PUD_DOWN
        mock.PUD_OFF = PUD_OFF
        mock.BOTH = BOTH
        mock.BCM = BCM
        yield mock

@pytest.fixture
def gpio_hardware(mock_gpio: Mock) -> GPIOHardware:
    """Creates a GPIOManager instance with mocked GPIO"""
    hardware = GPIOHardware()
    return hardware

@pytest.fixture
def mock_logger():
    with patch('features.gpio.hardware.logger') as mock:
        yield mock

class TestGPIOManager:
    
    def test_singleton_pattern(self, gpio_hardware: GPIOHardware):
        """Test that GPIOManager implements singleton pattern correctly"""
        manager1 = GPIOHardware()
        manager2 = GPIOHardware()
        assert manager1 is manager2
        assert manager1 is gpio_hardware
    
    def test_get_valid_pins_success(self, gpio_hardware: GPIOHardware):
        # Configure mock to return valid GPIO functions for certain pins
        def gpio_function_side_effect(pin: int) -> int:
            if pin in [2, 3, 4]:
                return IN
            elif pin in [17, 18, 27]:
                return OUT
            raise ValueError(f"Invalid pin {pin}")
            
        gpio_hardware.gpio.gpio_function.side_effect = gpio_function_side_effect
        
        valid_pins = gpio_hardware.get_valid_pins()
        assert valid_pins == [2, 3, 4, 17, 18, 27]
        
        # Test caching behavior
        gpio_hardware.gpio.gpio_function.side_effect = None  # Clear side effect
        cached_pins = gpio_hardware.get_valid_pins()
        assert cached_pins == valid_pins  # Should return cached result
        
    def test_get_valid_pins_no_pins(self, gpio_hardware: GPIOHardware):
        # Configure mock to return no valid pins
        gpio_hardware.gpio.gpio_function.side_effect = ValueError("Invalid pin")
        
        with pytest.raises(RuntimeError, match="No valid pins found"):
            gpio_hardware.get_valid_pins()

    def test_setup_input_pin_basic(self, gpio_hardware: GPIOHardware, mock_logger: Mock):
        pin = 18
        gpio_hardware.setup_input_pin(pin)
        
        gpio_hardware.gpio.setup.assert_called_once_with(
            pin, 
            IN,
            pull_up_down=PUD_OFF
        )
        mock_logger.info.assert_called_once_with(
            f"Setup pin {pin} as input with pull-up/pull-down value 'OFF'"
        )

    def test_setup_input_pin_with_edge_detection(self, gpio_hardware: GPIOHardware):
        pin = 18
        callback = Mock()
        bouncetime = 300
        
        gpio_hardware.setup_input_pin(
            pin=pin,
            edge_detection=True,
            pull_up_down=PUD_UP,
            bouncetime=bouncetime,
            callback=callback
        )
        
        gpio_hardware.gpio.setup.assert_called_once_with(
            pin,
            IN,
            pull_up_down=PUD_UP
        )
        
        # Verify event detection was set up
        gpio_hardware.gpio.add_event_detect.assert_called_once()
        args = gpio_hardware.gpio.add_event_detect.call_args
        assert args[0][0] == pin  # First positional arg should be pin
        assert args[1]["bouncetime"] == bouncetime
        
        # Test the wrapped callback
        # Configure mock to return HIGH state
        gpio_hardware.gpio.input.return_value = HIGH
        wrapped_callback = args[1]["callback"]  # Get the wrapped callback
        wrapped_callback(pin)  # Simulate edge detection
        
        # Verify our callback was called with both pin and state
        callback.assert_called_once_with(pin, HIGH)
        
        # Test with LOW state
        callback.reset_mock()
        gpio_hardware.gpio.input.return_value = LOW
        wrapped_callback(pin)  # Simulate edge detection again
        callback.assert_called_once_with(pin, LOW)

    def test_setup_input_pin_edge_detection_validation(self, gpio_hardware: GPIOHardware):
        # Test edge detection without callback
        with pytest.raises(ValueError, match="Callback must be provided with edge_detection=True"):
            gpio_hardware.setup_input_pin(18, edge_detection=True)

        # Test callback without edge detection
        callback = Mock()
        with pytest.raises(ValueError, match="must not be provided with edge_detection=False"):
            gpio_hardware.setup_input_pin(18, edge_detection=False, callback=callback)

    def test_setup_input_pin_invalid_pull_up_down(self, gpio_hardware: GPIOHardware):
        with pytest.raises(ValueError, match="Invalid pull-up/down value"):
            gpio_hardware.setup_input_pin(18, pull_up_down=999) # type: ignore

    def test_setup_output_pin_basic(self, gpio_hardware: GPIOHardware, mock_logger: Mock):
        pin = 18
        gpio_hardware.setup_output_pin(pin)
        
        gpio_hardware.gpio.setup.assert_called_once_with(
            pin,
            OUT,
            pull_up_down=PUD_OFF,
            initial=None
        )
        mock_logger.info.assert_called_once()

    def test_setup_output_pin_with_initial_state(self, gpio_hardware: GPIOHardware):
        pin = 18
        gpio_hardware.setup_output_pin(pin, initial_state=HIGH)
        
        gpio_hardware.gpio.setup.assert_called_once_with(
            pin,
            OUT,
            pull_up_down=PUD_OFF,
            initial=HIGH
        )

    def test_setup_output_pin_invalid_state(self, gpio_hardware: GPIOHardware):
        with pytest.raises(ValueError, match="Invalid initial state, must be HIGH or LOW"):
            gpio_hardware.setup_output_pin(18, initial_state=999)

    def test_set_output_state_success(self, gpio_hardware: GPIOHardware, mock_logger: Mock):
        """Test setting output state successfully"""
        pin = 18
        # Mock get_valid_pins to return our test pin
        gpio_hardware.get_valid_pins = lambda: [pin]
        
        # Test setting HIGH state
        gpio_hardware.set_output_state(pin, HIGH)
        gpio_hardware.gpio.output.assert_called_with(pin, HIGH)
        mock_logger.info.assert_called_with(f"Set pin {pin} state to {HIGH}")
        
        # Reset mock and test setting LOW state
        gpio_hardware.gpio.output.reset_mock()
        mock_logger.info.reset_mock()
        
        gpio_hardware.set_output_state(pin, LOW)
        gpio_hardware.gpio.output.assert_called_with(pin, LOW)
        mock_logger.info.assert_called_with(f"Set pin {pin} state to {LOW}")

    def test_set_output_state_invalid_pin(self, gpio_hardware: GPIOHardware):
        """Test setting output state with invalid pin"""
        # Mock get_valid_pins to return empty list
        gpio_hardware.get_valid_pins = lambda: []
        
        with pytest.raises(ValueError, match="Invalid pin number"):
            gpio_hardware.set_output_state(999, HIGH)

    def test_set_output_state_invalid_state(self, gpio_hardware: GPIOHardware):
        """Test setting output state with invalid state value"""
        pin = 18
        # Mock get_valid_pins to return our test pin
        gpio_hardware.get_valid_pins = lambda: [pin]
        
        with pytest.raises(ValueError, match="Invalid initial state, must be HIGH or LOW"):
            gpio_hardware.set_output_state(pin, 999)

    def test_get_pin_state_success(self, gpio_hardware: GPIOHardware):
        """Test getting pin state successfully"""
        pin = 18
        # Mock get_valid_pins to return our test pin
        gpio_hardware.get_valid_pins = lambda: [pin]
        
        # Test reading HIGH state
        gpio_hardware.gpio.input.return_value = HIGH
        state = gpio_hardware.get_pin_state(pin)
        assert state == HIGH
        gpio_hardware.gpio.input.assert_called_once_with(pin)
        
        # Reset mock and test reading LOW state
        gpio_hardware.gpio.input.reset_mock()
        gpio_hardware.gpio.input.return_value = LOW
        
        state = gpio_hardware.get_pin_state(pin)
        assert state == LOW
        gpio_hardware.gpio.input.assert_called_once_with(pin)

    def test_get_pin_state_invalid_pin(self, gpio_hardware: GPIOHardware):
        """Test getting state of invalid pin"""
        # Mock get_valid_pins to return empty list
        gpio_hardware.get_valid_pins = lambda: []
        
        with pytest.raises(ValueError, match="Invalid pin number"):
            gpio_hardware.get_pin_state(999)

    def test_cleanup(self, gpio_hardware: GPIOHardware, mock_logger: Mock):
        gpio_hardware.cleanup()
        gpio_hardware.gpio.cleanup.assert_called_once()
        mock_logger.info.assert_called_once_with("GPIO resources cleaned up")
        assert gpio_hardware._valid_pins is None  # Should reset cached pins

    def test_initialization(self, mock_gpio: Mock):
        """Test initialization is done correctly"""
        gpio = GPIOHardware()
        mock_gpio.setmode.assert_called_once_with(BCM)
        assert gpio._initialized is True 
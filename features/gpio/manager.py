"""
GPIO Manager Module

This module provides the core GPIO functionality with both real hardware and mock support.
"""
import platform
import logging
import os
from typing import Dict, List, Optional, Set, Callable
from .hardware import GPIO, get_valid_pins

# For real hardware
try:
    import RPi.GPIO as RPI_GPIO
except ImportError:
    RPI_GPIO = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPIOManager:
    """
    Manages GPIO operations with support for both real Raspberry Pi hardware and mock implementation.
    
    Attributes:
        is_raspberry_pi (bool): Whether running on actual Raspberry Pi hardware
        pins (Dict): Dictionary storing pin states and configurations
        _mock_states (Dict): Internal dictionary for mock pin states
        _pin_callbacks (Dict): Dictionary storing pin change callbacks
        _pin_modes (Dict): Cache of pin modes to avoid unnecessary reads
    """ 
    # Singleton instance
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPIOManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self): 
        """Initialize the GPIO manager with appropriate hardware detection."""
        # Only run initialization once
        if self._initialized:
            return
            
        # Check for Raspberry Pi model file
        is_pi = False
        if os.path.exists('/sys/firmware/devicetree/base/model'):
            with open('/sys/firmware/devicetree/base/model') as f:
                model = f.read()
                is_pi = model.startswith('Raspberry Pi')
        
        self.is_raspberry_pi = is_pi and RPI_GPIO is not None
        self.pins = {}  # Stores pin states for output pins
        self._pin_modes = {}  # Stores pin modes (IN/OUT)
        self._pin_callbacks = {}  # Stores callbacks for input pins
        self._initialized = False
        
        # Get valid pins for this hardware
        self.valid_pins = get_valid_pins()
        
        # Initialize all pins as unconfigured
        for pin in self.valid_pins:
            self._pin_modes[pin] = None
            self.pins[pin] = GPIO.LOW
        
        # Log hardware info
        if self.is_raspberry_pi and hasattr(RPI_GPIO, "RPI_INFO"):
            logger.info(f"Raspberry Pi Hardware Info:")
            for key, value in RPI_GPIO.RPI_INFO.items():
                logger.info(f"  {key}: {value}")
        
        # Initialize immediately
        self.setup()
        self._initialized = True

    def setup(self) -> None:
        """Set up GPIO system based on platform."""
        if self.is_raspberry_pi:
            try:
                RPI_GPIO.setmode(RPI_GPIO.BCM)
                #RPI_GPIO.setwarnings(False)  # Disable warnings about pin states
                logger.info("Initialized real Raspberry Pi GPIO in BCM mode")
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {str(e)}")
                raise RuntimeError(f"Hardware access failed: {str(e)}")
        else:
            self._initialized = True
            logger.info("Initialized mock GPIO")

    def _setup_mock(self) -> None: 
        """Set up mock GPIO implementation."""
        logger.info("Initialized mock GPIO implementation")
        # Initialize all pins with default state
        self._mock_states = {
            pin: {'mode': GPIO.IN, 'state': GPIO.LOW, 'configured': False}
            for pin in self.valid_pins
        }
        
        logger.info("GPIO cleanup completed")

    def get_available_pins(self) -> List[int]:
        """
        Get list of available GPIO pins.
        
        Returns:
            List[int]: List of valid GPIO pin numbers
        """
        return self.valid_pins
    
    def get_configured_pins(self) -> Dict[int, str]:
        """
        Get dictionary of configured pins and their modes.
        
        Returns:
            Dict[int, str]: Dictionary mapping pin numbers to their modes ('IN' or 'OUT')
        """
        if self.is_raspberry_pi:
            configured_pins = {}
            for pin in self.valid_pins:
                try:
                    mode = RPI_GPIO.gpio_function(pin)
                    if mode in [RPI_GPIO.IN, RPI_GPIO.OUT]:
                        configured_pins[pin] = "IN" if mode == RPI_GPIO.IN else "OUT"
                except Exception as e:
                    logger.debug(f"Pin {pin} not configured: {str(e)}")
                    continue
            return configured_pins
        else:
            return {
                pin: state['mode']
                for pin, state in self._mock_states.items()
                if state['configured']
            }

    def get_pin_state(self, pin: int) -> int:
        """
        Get the current state of a GPIO pin.
        
        Args:
            pin (int): The GPIO pin number
            
        Returns:
            int: GPIO.HIGH or GPIO.LOW
            
        Raises:
            ValueError: If pin is invalid
            RuntimeError: If pin is not configured
        """
        logger.debug(f"Getting state for pin {pin}")
        
        if pin not in self.valid_pins:
            logger.error(f"Invalid GPIO pin: {pin}")
            raise ValueError(f"Invalid GPIO pin: {pin}")
        
        if pin not in self._pin_modes:
            logger.error(f"Pin {pin} is not configured")
            raise RuntimeError(f"Pin {pin} is not configured")
        
        if self.is_raspberry_pi:
            mode = self._pin_modes.get(pin)
            if mode == GPIO.OUT:
                # For output pins, we maintain our own state tracking
                 # TODO: Do we need to set the default state here? Or why ist it LOW?
                state = self.pins.get(pin, GPIO.LOW)
                logger.debug(f"Output pin {pin} state from cache: {state}")
                return state
            else:
                # For input pins, we read directly
                try:
                    state = GPIO.HIGH if RPI_GPIO.input(pin) else GPIO.LOW
                    logger.debug(f"Input pin {pin} current state: {state}")
                    return state
                except Exception as e:
                    logger.error(f"Failed to read RPi pin {pin} state: {str(e)}")
                    raise RuntimeError(f"Failed to read pin state: {str(e)}")
        else:
            if not self._mock_states[pin]['configured']:
                logger.error(f"Mock pin {pin} is not configured")
                raise RuntimeError(f"Pin {pin} is not configured")
            state = self._mock_states[pin]['state']
            logger.debug(f"Mock pin {pin} state: {state}")
            return state

    def configure_pin(self, pin: int, mode: str, callback: Optional[Callable] = None) -> None:
        """
        Configure a GPIO pin with the specified mode and optional callback for input pins.
        
        Args:
            pin (int): The GPIO pin number
            mode (str): Either GPIO.IN or GPIO.OUT
            callback (Optional[Callable]): Callback function for input pin changes
            
        Raises:
            ValueError: If pin or mode is invalid
            RuntimeError: If hardware access fails
        """
        logger.info(f"Configuring pin {pin} as {mode}")
        
        if pin not in self.valid_pins:
            logger.error(f"Invalid GPIO pin: {pin}")
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if mode not in [GPIO.IN, GPIO.OUT]:
            logger.error(f"Invalid mode for pin {pin}: {mode}")
            raise ValueError(f"Invalid mode: {mode}")
            
        if self.is_raspberry_pi:
            try:
                # Convert string mode to RPi.GPIO mode
                rpi_mode = RPI_GPIO.IN if mode == GPIO.IN else RPI_GPIO.OUT
                logger.debug(f"Setting up RPi pin {pin} with mode {rpi_mode}")
                RPI_GPIO.setup(pin, rpi_mode)
                self._pin_modes[pin] = mode
                logger.info(f"Successfully configured pin {pin} as {mode}")
                
                if mode == GPIO.IN and callback:
                    logger.debug(f"Setting up callback for input pin {pin}")
                    # Remove any existing event detection
                    RPI_GPIO.remove_event_detect(pin)
                    # Add both rising and falling edge detection
                    RPI_GPIO.add_event_detect(pin, RPI_GPIO.BOTH, callback=callback)
                    self._pin_callbacks[pin] = callback
            except Exception as e:
                logger.error(f"Failed to configure RPi pin {pin}: {str(e)}")
                raise RuntimeError(f"Hardware configuration failed: {str(e)}")
        else:
            # Use hardware.GPIO for mock implementation
            logger.debug(f"Setting up mock pin {pin} with mode {mode}")
            GPIO.setup(pin, mode)  # This validates the pin and mode
            self._mock_states[pin]['mode'] = mode
            self._mock_states[pin]['configured'] = True
            if callback:
                self._pin_callbacks[pin] = callback
            logger.info(f"Successfully configured mock pin {pin} as {mode}")

    def set_pin_state(self, pin: int, state: int) -> None:
        """
        Set the state of a GPIO pin (only for output pins).
        
        Args:
            pin (int): The GPIO pin number
            state (int): GPIO.HIGH or GPIO.LOW
            
        Raises:
            ValueError: If pin or state is invalid, or if pin is not configured as output
            RuntimeError: If pin is not configured
        """
        logger.info(f"Setting pin {pin} state to {state}")
        
        if pin not in self.valid_pins:
            logger.error(f"Invalid GPIO pin: {pin}")
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if state not in [GPIO.LOW, GPIO.HIGH]:
            logger.error(f"Invalid state value for pin {pin}: {state}")
            raise ValueError(f"Invalid state value: {state}")
            
        # Check if pin is configured
        if self.is_raspberry_pi:
            mode = self._pin_modes.get(pin)
            logger.debug(f"Current mode for pin {pin}: {mode}")
            if not mode:
                logger.error(f"Pin {pin} is not configured")
                raise RuntimeError(f"Pin {pin} is not configured")
        else:
            if not self._mock_states[pin]['configured']:
                logger.error(f"Mock pin {pin} is not configured")
                raise RuntimeError(f"Pin {pin} is not configured")
            mode = self._mock_states[pin]['mode']
            logger.debug(f"Current mode for mock pin {pin}: {mode}")
            
        # Check if pin is output
        if mode != GPIO.OUT:
            logger.error(f"Cannot set state for pin {pin}: configured as {mode}, not as output")
            raise ValueError(f"Pin {pin} is not configured as output")
            
        # Set the state
        if self.is_raspberry_pi:
            try:
                logger.debug(f"Setting RPi pin {pin} to state {state}")
                RPI_GPIO.output(pin, state)
                self.pins[pin] = state  # Track output pin state
                logger.info(f"Successfully set pin {pin} to state {state}")
            except Exception as e:
                logger.error(f"Failed to set RPi pin {pin} state: {str(e)}")
                raise RuntimeError(f"Failed to set pin state: {str(e)}")
        else:
            self._mock_states[pin]['state'] = state
            logger.info(f"Successfully set mock pin {pin} to state {state}")

    def cleanup(self) -> None:
        """
        Clean up GPIO resources.
        
        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            if self.is_raspberry_pi:
                RPI_GPIO.cleanup()
                self.pins.clear()
                self._pin_modes.clear()
            else:
                GPIO.cleanup()
                # Reset all pins to default state
                self._mock_states = {
                    pin: {'mode': GPIO.IN, 'state': GPIO.LOW, 'configured': False}
                    for pin in self.valid_pins
                }
            self._pin_callbacks.clear()
        except Exception as e:
            raise RuntimeError(f"Cleanup failed: {str(e)}")
        logger.info("GPIO cleanup completed")

# Create the singleton instance
gpio_manager = GPIOManager()

# Export the instance rather than the class
__all__ = ['gpio_manager']

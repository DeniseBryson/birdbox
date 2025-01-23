"""
GPIO Manager Module

This module provides the core GPIO functionality with both real hardware and mock support.
"""
import platform
import logging
from typing import Dict, List, Optional
from .hardware import GPIO

# For real hardware
try:
    import RPi.GPIO as RPI_GPIO
except ImportError:
    RPI_GPIO = None

# Configure logging
logger = logging.getLogger(__name__)

class GPIOManager:
    """
    Manages GPIO operations with support for both real Raspberry Pi hardware and mock implementation.
    
    Attributes:
        is_raspberry_pi (bool): Whether running on actual Raspberry Pi hardware
        pins (Dict): Dictionary storing pin states and configurations
        _mock_states (Dict): Internal dictionary for mock pin states
    """
    
    def __init__(self):
        """Initialize the GPIO manager with appropriate hardware detection."""
        self.is_raspberry_pi = platform.machine() == 'armv7l' and RPI_GPIO is not None
        self.pins = {}
        self._mock_states = {}
        self.setup()
        
    def setup(self) -> None:
        """Set up GPIO system based on platform."""
        if self.is_raspberry_pi:
            try:
                RPI_GPIO.setmode(RPI_GPIO.BCM)
                logger.info("Initialized real Raspberry Pi GPIO")
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {str(e)}")
                raise RuntimeError(f"Hardware access failed: {str(e)}")
        else:
            self._setup_mock()
            
    def _setup_mock(self) -> None:
        """Set up mock GPIO implementation."""
        logger.info("Initialized mock GPIO implementation")
        # Initialize all pins with default state
        self._mock_states = {
            pin: {'mode': GPIO.IN, 'state': GPIO.LOW, 'configured': False}
            for pin in GPIO.VALID_PINS
        }
        
    def get_available_pins(self) -> List[int]:
        """
        Get list of available GPIO pins.
        
        Returns:
            List[int]: List of valid GPIO pin numbers
        """
        return GPIO.VALID_PINS
        
    def get_pin_state(self, pin: int) -> Dict:
        """
        Get the current state and configuration of a GPIO pin.
        
        Args:
            pin (int): GPIO pin number
            
        Returns:
            Dict: Pin state information including mode and current state
            
        Raises:
            ValueError: If pin number is invalid
            RuntimeError: If pin is not configured or hardware access fails
        """
        if pin not in GPIO.VALID_PINS:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if self.is_raspberry_pi:
            try:
                mode = RPI_GPIO.gpio_function(pin)
                state = RPI_GPIO.input(pin)
            except Exception as e:
                raise RuntimeError(f"Hardware access failed: {str(e)}")
        else:
            if pin not in self._mock_states:
                raise RuntimeError("Pin not configured")
            pin_data = self._mock_states[pin]
            mode = pin_data['mode']
            state = pin_data['state']
            
        return {
            'pin': pin,
            'mode': mode,
            'state': state,
            'name': f'GPIO{pin}',
            'configured': self._mock_states[pin].get('configured', True)
        }
        
    def configure_pin(self, pin: int, mode: str) -> Dict:
        """
        Configure a GPIO pin's mode.
        
        Args:
            pin (int): GPIO pin number
            mode (str): Pin mode ("IN" or "OUT")
            
        Returns:
            Dict: Updated pin state
            
        Raises:
            ValueError: If pin number or mode is invalid
            RuntimeError: If hardware access fails
        """
        if pin not in GPIO.VALID_PINS:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if mode not in [GPIO.IN, GPIO.OUT]:
            raise ValueError(f"Invalid mode: {mode}")
            
        try:
            if self.is_raspberry_pi:
                RPI_GPIO.setup(pin, RPI_GPIO.IN if mode == GPIO.IN else RPI_GPIO.OUT)
            else:
                GPIO.setup(pin, mode)
                self._mock_states[pin] = {
                    'mode': mode,
                    'state': GPIO.LOW,
                    'configured': True
                }
        except Exception as e:
            raise RuntimeError(f"Hardware access failed: {str(e)}")
            
        return self.get_pin_state(pin)
        
    def set_pin_state(self, pin: int, state: int) -> Dict:
        """
        Set the state of a GPIO pin.
        
        Args:
            pin (int): GPIO pin number
            state (int): Pin state (0 or 1)
            
        Returns:
            Dict: Updated pin state
            
        Raises:
            ValueError: If pin number or state is invalid
            RuntimeError: If hardware access fails or pin is not configured
        """
        if pin not in GPIO.VALID_PINS:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if state not in [GPIO.LOW, GPIO.HIGH]:
            raise ValueError(f"Invalid state value: {state}")
            
        pin_data = self._mock_states.get(pin)
        if not pin_data or not pin_data.get('configured'):
            raise RuntimeError("Pin not configured")
            
        if pin_data['mode'] == GPIO.IN:
            raise ValueError("Cannot set state of input pin")
            
        try:
            if self.is_raspberry_pi:
                RPI_GPIO.output(pin, state)
            else:
                GPIO.output(pin, state)
                self._mock_states[pin]['state'] = state
        except Exception as e:
            raise RuntimeError(f"Hardware access failed: {str(e)}")
            
        return self.get_pin_state(pin)
        
    def cleanup(self) -> None:
        """
        Clean up GPIO resources.
        
        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            if self.is_raspberry_pi:
                RPI_GPIO.cleanup()
            else:
                GPIO.cleanup()
                # Reset all pins to default state
                self._mock_states = {
                    pin: {'mode': GPIO.IN, 'state': GPIO.LOW, 'configured': False}
                    for pin in GPIO.VALID_PINS
                }
        except Exception as e:
            raise RuntimeError(f"Cleanup failed: {str(e)}")
        logger.info("GPIO cleanup completed")
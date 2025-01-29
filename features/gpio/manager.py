"""
GPIO Manager Module

This module provides the core GPIO functionality with both real hardware and mock support.
"""
import platform
import logging
import os
from typing import Dict, List, Optional, Set
from .hardware import GPIO, get_valid_pins

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
        # Check for Raspberry Pi model file
        is_pi = False
        if os.path.exists('/sys/firmware/devicetree/base/model'):
            with open('/sys/firmware/devicetree/base/model') as f:
                model = f.read()
                is_pi = model.startswith('Raspberry Pi')
        
        self.is_raspberry_pi = is_pi and RPI_GPIO is not None
        self.pins = {}
        self._mock_states = {}
        
        # Get valid pins for this hardware
        self.valid_pins = get_valid_pins()
        
        # Log hardware info
        if self.is_raspberry_pi and hasattr(RPI_GPIO, "RPI_INFO"):
            logger.info(f"Raspberry Pi Hardware Info:")
            for key, value in RPI_GPIO.RPI_INFO.items():
                logger.info(f"  {key}: {value}")
            logger.info(f"Available GPIO pins: {self.valid_pins}")
        else:
            logger.info("Running in mock mode with simulated GPIO")
            logger.info(f"Available GPIO pins: {self.valid_pins}")
        
        self.setup()
        
    def setup(self) -> None:
        """Set up GPIO system based on platform."""
        if self.is_raspberry_pi:
            try:
                RPI_GPIO.setmode(RPI_GPIO.BCM)
                logger.info("Initialized real Raspberry Pi GPIO in BCM mode")
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
            for pin in self.valid_pins
        }
        
    def get_available_pins(self) -> List[int]:
        """
        Get list of available GPIO pins.
        
        Returns:
            List[int]: List of valid GPIO pin numbers
        """
        return self.valid_pins
        
    def get_configured_pins(self) -> Dict[int, str]:
        """
        Get dictionary of configured pins and their modes using direct GPIO access.
        
        Returns:
            Dict[int, str]: Dictionary mapping pin numbers to their modes ('IN' or 'OUT')
            
        Note:
            For mock environment, returns pins that have been explicitly configured
        """
        if self.is_raspberry_pi:
            configured_pins = {}
            for pin in self.valid_pins:
                try:
                    # Check if pin is setup by trying to get its function
                    mode = RPI_GPIO.gpio_function(pin)
                    if mode in [RPI_GPIO.IN, RPI_GPIO.OUT]:
                        configured_pins[pin] = "IN" if mode == RPI_GPIO.IN else "OUT"
                except Exception as e:
                    logger.debug(f"Pin {pin} not configured: {str(e)}")
                    continue
            return configured_pins
        else:
            # For mock environment, return pins that have been explicitly configured
            return {
                pin: state['mode']
                for pin, state in self._mock_states.items()
                if state['configured']
            }
        
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
        if pin not in self.valid_pins:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if self.is_raspberry_pi:
            try:
                mode = RPI_GPIO.gpio_function(pin)
                if mode not in [RPI_GPIO.IN, RPI_GPIO.OUT]:
                    raise RuntimeError(f"Pin {pin} is not configured as INPUT or OUTPUT")
                state = RPI_GPIO.input(pin)
                return {
                    'pin': pin,
                    'mode': "IN" if mode == RPI_GPIO.IN else "OUT",
                    'state': state,
                    'name': f'GPIO{pin}',
                    'configured': True
                }
            except Exception as e:
                logger.error(f"Failed to get pin {pin} state: {str(e)}")
                raise RuntimeError(f"Failed to access pin {pin}: {str(e)}")
        else:
            if pin not in self._mock_states:
                raise RuntimeError("Pin not configured")
            pin_data = self._mock_states[pin]
            return {
                'pin': pin,
                'mode': pin_data['mode'],
                'state': pin_data['state'],
                'name': f'GPIO{pin}',
                'configured': pin_data.get('configured', True)
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
        if pin not in self.valid_pins:
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
        if pin not in self.valid_pins:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if state not in [GPIO.LOW, GPIO.HIGH]:
            raise ValueError(f"Invalid state value: {state}")
            
        if self.is_raspberry_pi:
            try:
                # Check if pin is configured as output
                mode = RPI_GPIO.gpio_function(pin)
                if mode != RPI_GPIO.OUT:
                    raise ValueError("Cannot set state of input pin")
                    
                RPI_GPIO.output(pin, state)
            except Exception as e:
                raise RuntimeError(f"Hardware access failed: {str(e)}")
        else:
            pin_data = self._mock_states.get(pin)
            if not pin_data or not pin_data.get('configured'):
                raise RuntimeError("Pin not configured")
                
            if pin_data['mode'] == GPIO.IN:
                raise ValueError("Cannot set state of input pin")
                
            GPIO.output(pin, state)
            self._mock_states[pin]['state'] = state
            
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
                    for pin in self.valid_pins
                }
        except Exception as e:
            raise RuntimeError(f"Cleanup failed: {str(e)}")
        logger.info("GPIO cleanup completed")
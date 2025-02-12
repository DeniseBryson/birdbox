"""
GPIO Manager Module

This module provides the core GPIO functionality for Raspberry Pi hardware.
"""
import logging
import os
from typing import Dict, List, Optional
from .hardware import (
    GPIOHardware, HIGH, LOW, IN, OUT, UNDEFINED,
    PinMode, PinState, EventCallback
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create hardware interface
HW = GPIOHardware()

class GPIOManager:
    """
    Manages GPIO operations for Raspberry Pi hardware.
    
    Attributes:
        is_raspberry_pi (bool): Whether running on actual Raspberry Pi hardware
        pins (Dict): Dictionary storing pin states and configurations
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
        """Initialize the GPIO manager."""
        # Only run initialization once
        if self._initialized:
            return
            
        # Check for Raspberry Pi model file
        if os.path.exists('/sys/firmware/devicetree/base/model'):
            with open('/sys/firmware/devicetree/base/model') as f:
                model = f.read()
                self.is_raspberry_pi = model.startswith('Raspberry Pi')
        
        self._pin_modes: Dict[int, PinMode|None] = {}  # Stores pin modes (IN/OUT)
        self._output_pin_states: Dict[int, PinState] = {}  # Stores pin states for output pins
        self._output_pin_callbacks: Dict[int, EventCallback] = {}  # Stores callbacks for output pins
        
        # Initialize all pins as unconfigured
        for pin in self.valid_pins:
            self._pin_modes[pin] = None
            self._output_pin_states[pin] = LOW
        
        # Log hardware info
        if self.is_raspberry_pi and hasattr(HW, "RPI_INFO"):
            logger.info(f"Raspberry Pi Hardware Info:")
            for key, value in HW.RPI_INFO.items():
                logger.info(f"  {key}: {value}")
        
        self._initialized = True

    @property
    def valid_pins(self) -> List[int]:
        """Get list of valid GPIO pins."""
        return HW.get_valid_pins()

    def configure_pin(self, pin: int, mode: PinMode, callback: Optional[EventCallback] = None) -> None:
        """
        Configure a GPIO pin with the specified mode and optional callback for input pins.
        
        Args:
            pin (int): The GPIO pin number
            mode (int): Either IN or OUT
            callback (Optional[Callable]): Callback function for input pin changes
            
        Raises:
            ValueError: If pin or mode is invalid
            RuntimeError: If hardware access fails
        """
        logger.info(f"Configuring pin {pin} as {'IN' if mode == IN else 'OUT'}")

        if mode == IN:
            try:
                HW.setup_input_pin(pin, edge_detection=(callback is not None), callback=callback)
                self._pin_modes[pin] = mode
                logger.info(f"Successfully configured pin {pin} as {'IN' if mode == IN else 'OUT'}")
            except Exception as e:
                logger.error(f"Failed to configure pin {pin}: {str(e)}")
                raise RuntimeError(f"Hardware configuration failed: {str(e)}")
        else:
            try:
                init_state= HIGH 
                HW.setup_output_pin(pin, initial_state=init_state) 
                self._pin_modes[pin] = mode
                logger.info(f"Successfully configured pin {pin} as {'IN' if mode == IN else 'OUT'}")
                if callback:
                    self._output_pin_callbacks[pin] = callback
                    logger.info(f"Successfully registered callback for pin {pin}")
                self._output_pin_states[pin] = HIGH
                logger.info(f"Setting initial state of configured pin {pin} to HIGH")
                if callback:
                    callback(pin, init_state)  # Trigger callback to initialize state
            except Exception as e:
                logger.error(f"Failed to configure pin {pin}: {str(e)}")
                raise RuntimeError(f"Hardware configuration failed: {str(e)}")
    
    def get_configured_pins(self) -> Dict[int, PinMode]:
        """
        Get dictionary of configured pins and their modes.
        
        Returns:
            Dict[int, PinMode]: Dictionary mapping pin numbers to their modes (IN or OUT)
        """
        
        return {pin: mode for pin, mode in self._pin_modes.items() if mode is not None}
    
    def set_pin_state(self, pin: int, state: PinState) -> None:
        """
        Set the state of a GPIO pin (only for output pins).
        
        Args:
            pin (int): The GPIO pin number
            state (int): HIGH or LOW
            
        Raises:
            ValueError: If pin or state is invalid, or if pin is not configured as output
            RuntimeError: If pin is not configured
        """
        logger.info(f"Setting pin {pin} state to {'HIGH' if state == HIGH else 'LOW'}")
        
        # Check if pin is configured
        mode = self._pin_modes.get(pin, None)
        if mode is None:
            logger.error(f"Pin {pin} is not configured")
            raise RuntimeError(f"Pin {pin} is not configured")
        
        if mode not in [IN, OUT]:
            logger.error(f"Pin {pin} is not configured as input or output")
            raise ValueError(f"Pin {pin} is not configured as input or output")
        
        # Check if pin is input
        if mode != OUT:
            logger.error(f"Cannot set state for input pin {pin}")
            raise ValueError(f"Pin {pin} is not configured as output")
            
        # Set the state
        try:
            HW.set_output_state(pin, state)
            self._output_pin_states[pin] = state  # Track output pin state
            logger.info(f"Set pin {pin} to state {state}")
            callback = self._output_pin_callbacks.get(pin, None)
            if callback:
                callback(pin, state)  # Trigger callback with updated state
                logger.info(f"Triggered callback for output pin {pin} with state {state}")
        except Exception as e:
            logger.error(f"Failed to set pin {pin} state: {str(e)}")
            raise RuntimeError(f"Failed to set pin state: {str(e)}")
    
    def get_pin_state(self, pin: int) -> PinState:
        """
        Get the current state of a GPIO pin.
        
        Args:
            pin (int): The GPIO pin number
            
        Returns:
            PinState: HIGH or LOW or UNDEFINED if pin is invalid, not configured or any other error occurs
            
        """
        logger.debug(f"Getting state for pin {pin}")
        
        if pin not in self.valid_pins:
            logger.error(f"Invalid GPIO pin: {pin}")
            return UNDEFINED
        
        mode = self._pin_modes.get(pin, None)
        if mode is None:
            logger.error(f"Pin {pin} is not configured")
            return UNDEFINED
        
        if mode is OUT:
            # For output pins, we maintain our own state tracking
            state = self._output_pin_states.get(pin, None)
            if state is None:
                logger.error(f"Pin {pin} is not configured as output, but was found in _pin_modes")
                return UNDEFINED
            logger.debug(f"Output pin {pin} state from cache: {state}")
            return state
        
        if mode is IN:
            # For input pins, we read directly
            try:
                state = HW.get_pin_state(pin)
                logger.debug(f"Input pin {pin} current state: {state}")
                return state
            except Exception as e:
                logger.debug(f"Failed to read input pin {pin}: {str(e)}")
                return UNDEFINED
        return UNDEFINED
   
    def cleanup(self) -> None:
        """
        Clean up GPIO resources.
        
        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            HW.cleanup()
            self._output_pin_states.clear()
            self._pin_modes.clear()
            self._output_pin_callbacks.clear()
        except Exception as e:
            raise RuntimeError(f"Cleanup failed: {str(e)}")
        logger.info("GPIO cleanup completed")

# Create the singleton instance
gpio_manager = GPIOManager()

# Export the instance rather than the class
__all__ = ['gpio_manager']

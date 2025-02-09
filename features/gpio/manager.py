"""
GPIO Manager Module

This module provides the core GPIO functionality for Raspberry Pi hardware.
"""
import platform
import logging
import os
from typing import Dict, List
from .hardware import GPIOHardware as HW

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



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
        
        self._pin_modes: Dict[int, HW.PinMode] = {}  # Stores pin modes (IN/OUT)
        self.output_pin_states: Dict[int, HW.PinState] = {}  # Stores pin states for output pins
        self._output_pin_callbacks: Dict[int, HW.EventCallback] = {}  # Stores callbacks for output pins (input callbacks are handled    by hardware)
        
            # Initialize all pins as unconfigured
        for pin in self.valid_pins:
            self._pin_modes[pin] = None
            self.output_pin_states[pin] = HW.LOW
        
        # Log hardware info
        if self.is_raspberry_pi and hasattr(HW, "RPI_INFO"):
            logger.info(f"Raspberry Pi Hardware Info:")
            for key, value in HW.RPI_INFO.items():
                logger.info(f"  {key}: {value}")
        
        # Initialize GPIO
        self.setup()
        self._initialized = True

    def setup(self) -> None:
        """Set up GPIO system."""
        try:
            HW.setmode(HW.BCM)
            logger.info("Initialized Raspberry Pi GPIO in BCM mode")
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {str(e)}")
            raise RuntimeError(f"Hardware access failed: {str(e)}")

    def get_available_pins(self) -> List[int]:
        """
        Get list of available GPIO pins.
        
        Returns:
            List[int]: List of valid GPIO pin numbers
        """
        return HW.get_valid_pins()

    def configure_pin(self, pin: int, mode: HW.IN | HW.OUT, callback: HW.EventCallback) -> None:
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

        if mode==HW.IN:
            try:
                HW.setup_input_pin(pin, edge_detection=(callback is not None), callback=callback,)
                self._pin_modes[pin] = mode
                logger.info(f"Successfully configured pin {pin} as {mode.name}")
            except Exception as e:
                logger.error(f"Failed to configure pin {pin}: {str(e)}")
                raise RuntimeError(f"Hardware configuration failed: {str(e)}")
        else:
            try:
                HW.setup_output_pin(pin, initial_state=HW.HIGH)
                self._pin_modes[pin] = mode
                logger.info(f"Successfully configured pin {pin} as {mode.name}")
                self._output_pin_callbacks[pin] = callback
                logger.info(f"Successfully registered callback for pin {pin}")
                self.output_pin_states[pin] = HW.HIGH
                logger.info(f"Setting initial state of configured pin {pin} to {HW.HIGH}")
                self._output_pin_callbacks[pin](pin) # Trigger callback to initialize state
            except Exception as e:
                logger.error(f"Failed to configure pin {pin}: {str(e)}")
                raise RuntimeError(f"Hardware configuration failed: {str(e)}")
    
    def get_configured_pins(self) -> Dict[int, str]:
        """
        Get dictionary of configured pins and their modes.
        
        Returns:
            Dict[int, HW.PinMode]: Dictionary mapping pin numbers to their modes (HW.IN or HW.OUT)
        """
  
        return self._pin_modes
    
    def set_pin_state(self, pin: int, state: HW.PinState) -> None:
        """
        Set the state of a GPIO pin (only for output pins).
        
        Args:
            pin (int): The GPIO pin number
            state (HW.PinState): GPIO.HIGH or GPIO.LOW
            
        Raises:
            ValueError: If pin or state is invalid, or if pin is not configured as output
            RuntimeError: If pin is not configured
        """
        logger.info(f"Setting pin {pin} state to {state}")
        
        # Check if pin is configured
        mode = self._pin_modes.get(pin, None)
        if not mode:
            logger.error(f"Pin {pin} is not configured")
            raise RuntimeError(f"Pin {pin} is not configured")
        
        if mode not in [HW.IN, HW.OUT]:
            logger.error(f"Pin {pin} is not configured as input or output")
            raise ValueError(f"Pin {pin} is not configured as input or output")
        
        # Check if pin is input
        if mode != HW.OUT:
            logger.error(f"Cannot set state for input pin {pin}")
            raise ValueError(f"Pin {pin} is not configured as output")
            
        # Set the state
        try:
            HW.set_output_state(pin, state)
            self.output_pin_states[pin] = state  # Track output pin state
            logger.info(f"Set pin {pin} to state {state}")
            callback = self._output_pin_callbacks.get(pin, None)
            if callback:
                self._output_pin_callbacks[pin](pin) # Trigger callback to initialize state
                logger.info(f"Triggered callback for output pin {pin}")
        except Exception as e:
            logger.error(f"Failed to set pin {pin} state: {str(e)}")
            raise RuntimeError(f"Failed to set pin state: {str(e)}")
    
    def get_pin_state(self, pin: int) -> HW.PinState:
        """
        Get the current state of a GPIO pin.
        
        Args:
            pin (int): The GPIO pin number
            
        Returns:
            HW.PinState: GPIO.HIGH or GPIO.LOW or UNDEFINED if pin is invalid, not configured or any other error occurs
            
        """
        logger.debug(f"Getting state for pin {pin}")
        
        if pin not in HW.get_valid_pins():
            logger.error(f"Invalid GPIO pin: {pin}")
            return HW.UNDEFINED
        
        mode = self._pin_modes.get(pin, None)
        if mode is None:
            logger.error(f"Pin {pin} is not configured")
            return HW.UNDEFINED
        
        if mode == HW.OUT:
            # For output pins, we maintain our own state tracking
            state = self.output_pin_states.get(pin, None)
            if state is None:
                logger.error(f"Pin {pin} is not configured as output, but was found in _pin_modes")
                return HW.UNDEFINED
            logger.debug(f"Output pin {pin} state from cache: {state}")
            return state
        
        if mode == HW.IN:
            # For input pins, we read directly
            try:
                state = HW.get_pin_state(pin)
                logger.debug(f"Input pin {pin} current state: {state}")
                return state
            except Exception as e:
                logger.debug(f"Failed to read input pin {pin}: {str(e)}")
                return HW.UNDEFINED
    
    def cleanup(self) -> None:
        """
        Clean up GPIO resources.
        
        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            HW.cleanup()
            self.output_pin_states.clear()
            self._pin_modes.clear()
            self._output_pin_callbacks.clear()
        except Exception as e:
            raise RuntimeError(f"Cleanup failed: {str(e)}")
        logger.info("GPIO cleanup completed")

# Create the singleton instance
gpio_manager = GPIOManager()

# Export the instance rather than the class
__all__ = ['gpio_manager']

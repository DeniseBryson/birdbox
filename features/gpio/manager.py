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
logger = logging.getLogger(__name__)

class GPIOManager:
    """
    Manages GPIO operations with support for both real Raspberry Pi hardware and mock implementation.
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

    def setup(self) -> None:
        """Set up GPIO system based on platform."""
        if self.is_raspberry_pi:
            try:
                # Check if mode is already set
                current_mode = RPI_GPIO.getmode()
                if current_mode is None:
                    # Only clean up if no mode is set
                    RPI_GPIO.cleanup()
                    RPI_GPIO.setmode(RPI_GPIO.BCM)
                elif current_mode != RPI_GPIO.BCM:
                    # If wrong mode, raise error
                    raise RuntimeError(f"GPIO mode already set to {current_mode}, but BCM mode is required")
                
                RPI_GPIO.setwarnings(False)
                self._initialized = True
                logger.info("Initialized real Raspberry Pi GPIO in BCM mode")
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {str(e)}")
                raise RuntimeError(f"Hardware access failed: {str(e)}")
        else:
            self._initialized = True
            logger.info("Initialized mock GPIO")

    def get_pin_state(self, pin: int) -> int:
        """Get the current state of a GPIO pin."""
        if pin not in self.valid_pins:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        mode = self._pin_modes.get(pin)
        if mode is None:
            raise RuntimeError(f"Pin {pin} is not configured")
            
        if self.is_raspberry_pi:
            if mode == GPIO.OUT:
                return self.pins[pin]  # Return cached state for output pins
            else:
                try:
                    return GPIO.HIGH if RPI_GPIO.input(pin) else GPIO.LOW
                except Exception as e:
                    logger.error(f"Failed to read pin {pin}: {str(e)}")
                    raise RuntimeError(f"Failed to read pin {pin}: {str(e)}")
        else:
            return self.pins[pin]  # In mock mode, always return cached state

    def configure_pin(self, pin: int, mode: str, callback: Optional[Callable] = None) -> None:
        """Configure a GPIO pin with the specified mode."""
        if not self._initialized:
            raise RuntimeError("GPIO system not initialized")
            
        if pin not in self.valid_pins:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if mode not in [GPIO.IN, GPIO.OUT]:
            raise ValueError(f"Invalid mode: {mode}")
            
        if self.is_raspberry_pi:
            try:
                RPI_GPIO.setup(pin, RPI_GPIO.IN if mode == GPIO.IN else RPI_GPIO.OUT)
                self._pin_modes[pin] = mode
                
                if mode == GPIO.IN and callback:
                    RPI_GPIO.remove_event_detect(pin)
                    RPI_GPIO.add_event_detect(pin, RPI_GPIO.BOTH, callback=callback)
                    self._pin_callbacks[pin] = callback
            except Exception as e:
                logger.error(f"Failed to configure pin {pin}: {str(e)}")
                raise RuntimeError(f"Failed to configure pin {pin}: {str(e)}")
        else:
            self._pin_modes[pin] = mode
            if callback:
                self._pin_callbacks[pin] = callback

    def set_pin_state(self, pin: int, state: int) -> None:
        """Set the state of a GPIO pin (only for output pins)."""
        if pin not in self.valid_pins:
            raise ValueError(f"Invalid GPIO pin: {pin}")
            
        if state not in [GPIO.LOW, GPIO.HIGH]:
            raise ValueError(f"Invalid state value: {state}")
            
        mode = self._pin_modes.get(pin)
        if mode is None:
            raise RuntimeError(f"Pin {pin} is not configured")
        if mode != GPIO.OUT:
            raise ValueError(f"Pin {pin} is not configured as output")
            
        if self.is_raspberry_pi:
            try:
                RPI_GPIO.output(pin, state)
                self.pins[pin] = state
            except Exception as e:
                logger.error(f"Failed to set pin {pin} state: {str(e)}")
                raise RuntimeError(f"Failed to set pin {pin} state: {str(e)}")
        else:
            self.pins[pin] = state

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            if self.is_raspberry_pi and self._initialized:
                # Only clean up configured pins
                configured_pins = [pin for pin, mode in self._pin_modes.items() if mode is not None]
                if configured_pins:
                    for pin in configured_pins:
                        try:
                            RPI_GPIO.cleanup(pin)
                        except:
                            pass
            
            # Reset all pin states
            for pin in self.valid_pins:
                self._pin_modes[pin] = None
                self.pins[pin] = GPIO.LOW
            
            self._pin_callbacks.clear()
            self._initialized = False
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise RuntimeError(f"Cleanup failed: {str(e)}")
        
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
        configured = {}
        for pin in self.valid_pins:
            mode = self._pin_modes.get(pin)
            if mode is not None:
                configured[pin] = mode
        return configured
"""
GPIO Manager Module

This module provides the core GPIO functionality for Raspberry Pi hardware.
"""
import logging
import os
from typing import Dict, List, Optional, Set, NamedTuple

from .constants import HIGH, IN, OUT, UNDEFINED, PinMode, PinState, EventCallback, IS_RASPBERRYPI
from .hardware import  GPIOHardware, PWMInfo


# Configure logging
#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create hardware interface
HW = GPIOHardware()

class CallbackInfo(NamedTuple):
    """
    Container for callback information.
    
    Attributes:
        on_change: Callback function called when pin state changes
        on_clear: Optional callback function called when the callback is removed
    """
    on_change: EventCallback
    on_clear: Optional[EventCallback] = None

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
        self._pin_callbacks: Dict[int, Set[CallbackInfo]] = {}  # Stores all callbacks for all pins
        self._pwm_pins: Dict[int, PWMInfo] = {}  # Stores PWM objects for PWM pins

        # Initialize all pins as unconfigured
        valid_pins = self.get_valid_pins()
        logger.info(f"Initial valid pins found: {valid_pins}")
        for pin in (valid_pins):
            self._pin_modes[pin] = None
            self._pin_callbacks[pin] = set()
        logger.info(f"Initial pin modes: {self._pin_modes}")
        logger.info(f"Initial output pin states: {self._output_pin_states}")
        
        # Log hardware info
        if IS_RASPBERRYPI and hasattr(HW, "RPI_INFO"):
            logger.info(f"Raspberry Pi Hardware Info:")
            for key, value in HW.RPI_INFO.items():
                logger.info(f"  {key}: {value}")
        
        logger.info(f"Initial pin callbacks: {self._pin_callbacks}")

        self._initialized = True

    def get_valid_pins(self) -> List[int]:
        """Get list of valid GPIO pins."""
        return HW.get_valid_pins()

    def configure_pin(self, pin: int, mode: PinMode, callback: Optional[EventCallback] = None, on_clear: Optional[EventCallback] = None) -> None:
        """
        Configure a GPIO pin with the specified mode and optional callbacks.
        A pin can only be configured once. Use clear_pin() to reset configuration.
        
        Args:
            pin (int): The GPIO pin number
            mode (int): Either IN or OUT
            callback (Optional[Callable]): Optional callback function for pin changes
            on_clear (Optional[Callable]): Optional callback function called when the callback is removed
            
        Raises:
            ValueError: If pin or mode is invalid
            RuntimeError: If pin is already configured or hardware access fails
        """
        logger.info(f"Configuring pin {pin} as {'IN' if mode == IN else 'OUT'}")
        
        # Check if pin is already configured
        current_mode = self._pin_modes.get(pin, None)
        if current_mode is not None:
            raise RuntimeError(f"Pin {pin} is already configured as {current_mode}. Use clear_pin() first to reconfigure.")

        if mode == IN:
            try:
                # Create a wrapper that will call all registered callbacks
                def input_callback(pin: int, state: PinState) -> None:
                    for cb_info in self._pin_callbacks[pin]:
                        try:
                            cb_info.on_change(pin, state)
                        except Exception as e:
                            logger.error(f"Error in callback for pin {pin}: {e}")
                        
                HW.setup_input_pin(pin, edge_detection=True, callback=input_callback)
                self._pin_modes[pin] = mode
                if callback:
                    self._pin_callbacks[pin].add(CallbackInfo(on_change=callback, on_clear=on_clear))
                logger.info(f"Successfully configured pin {pin} as 'IN'{' including callback' if callback is not None else ''}")

            except Exception as e:
                logger.error(f"Failed to configure pin {pin}: {str(e)}")
                raise RuntimeError(f"Hardware configuration failed: {str(e)}")
        
        if mode == OUT:
            try:
                init_state = HIGH
                HW.setup_output_pin(pin, initial_state=init_state) 
                self._pin_modes[pin] = mode
                self._output_pin_states[pin] = init_state
                if callback:
                    self._pin_callbacks[pin].add(CallbackInfo(on_change=callback, on_clear=on_clear))
                logger.info(f"Successfully configured pin {pin} as 'OUT' with initial state {init_state}")
            except Exception as e:
                logger.error(f"Failed to configure pin {pin}: {str(e)}")
                raise RuntimeError(f"Hardware configuration failed: {str(e)}")
        
        # Trigger initial callback if provided
        if callback:
            logger.info(f"Triggering initial callback for pin {pin}")
            try:
                callback(pin, self.get_pin_state(pin))
            except Exception as e:
                logger.error(f"Error in initial callback for pin {pin}: {e}")

    def watch_pin(self, pin: int, callback: EventCallback, on_clear: Optional[EventCallback] = None) -> None:
        """
        Add a callback to watch a pin's state changes without modifying its configuration.
        
        Args:
            pin (int): The GPIO pin number
            callback (Callable): Callback function for pin changes
            on_clear (Optional[Callable]): Optional callback function called when the callback is removed
            
        Raises:
            RuntimeError: If pin is not configured
        """
        if pin not in self._pin_modes or self._pin_modes[pin] is None:
            logger.warning(f"Pin {pin} is not (yet) configured, still added watch callback.")
        if pin not in self.get_valid_pins():
            raise ValueError(f"Invalid pin number: {pin}")
        
        callback_info = CallbackInfo(on_change=callback, on_clear=on_clear)
        self._pin_callbacks[pin].add(callback_info)
        logger.info(f"Added callback for pin {pin}")
        try:
            # Trigger initial callback with current state
            callback(pin, self.get_pin_state(pin))
        except Exception as e:
            logger.error(f"Error in initial callback for pin {pin}: {e}")

    def clear_pin(self, pin: int) -> None:
        """
        Clear a pin's configuration and all associated callbacks.
        After clearing, the pin can be configured again.
        
        Args:
            pin (int): The GPIO pin number
            
        Raises:
            ValueError: If pin is invalid
            RuntimeError: If hardware cleanup fails
        """
        if pin not in self.get_valid_pins():
            raise ValueError(f"Invalid pin number: {pin}")
            
        # Call onClear callbacks before removing them
        for callback_info in self._pin_callbacks[pin]:
            if callback_info.on_clear:
                try:
                    callback_info.on_clear(pin, self.get_pin_state(pin))
                except Exception as e:
                    logger.error(f"Error in onClear callback for pin {pin}: {e}")
        
        # Remove all callbacks
        self._pin_callbacks[pin].clear()
        
        # Clear output state if it was an output pin
        self._output_pin_states.pop(pin, None)
        
        # Clear pin mode
        self._pin_modes[pin] = None
        
        # Remove hardware configuration
        try:
            HW.cleanup(pin=pin)
            logger.info(f"Cleared configuration for pin {pin}")
        except Exception as e:
            logger.error(f"Failed to clear pin {pin}: {str(e)}")
            raise RuntimeError(f"Hardware cleanup failed: {str(e)}")

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
            RuntimeError: If pin is not configured or hardware access fails
        """
        
        # Check if pin is configured
        mode = self._pin_modes.get(pin, None)
        if mode is None:
            logger.error(f"Pin {pin} is not configured")
            raise RuntimeError(f"Pin {pin} is not configured")
        
        if mode not in [IN, OUT]:
            logger.error(f"Pin {pin} is not configured as input or output")
            raise ValueError(f"Pin {pin} is not configured as input or output")
        
        if mode != OUT:
            logger.error(f"Cannot set state for input pin {pin}")
            raise ValueError(f"Pin {pin} is not configured as output")
            
        # Set the state
        logger.info(f"Setting pin {pin} state to {'HIGH' if state == HIGH else 'LOW'}")
        try:
            HW.set_output_state(pin, state)
            self._output_pin_states[pin] = state  # Track output pin state
            
            # Trigger all callbacks
            for callback_info in self._pin_callbacks[pin]:
                try:
                    callback_info.on_change(pin, state)
                    logger.debug(f"Triggered callback for output pin {pin} with state {state}")
                except Exception as e:
                    logger.error(f"Error in callback for pin {pin}: {e}")
                    
            logger.info(f"Set pin {pin} to state {state}")
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
        
        if pin not in self.get_valid_pins():
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
   
    def setup_pwm(self, pin: int, frequency: int) -> None:
        """
        Set up PWM for a GPIO pin.
        
        Args:
            pin (int): The GPIO pin number
            frequency (int): The frequency of the PWM signal
        """
        if pin not in self.get_valid_pins():
            logger.error(f"Invalid GPIO pin: {pin}")
            raise ValueError(f"Invalid GPIO pin: {pin}")
        
        pin_mode = self._pin_modes.get(pin, None)
        if pin_mode is None:
            logger.error(f"Pin {pin} is not configured")
            raise ValueError(f"Pin {pin} is not configured")
        
        if pin_mode != OUT:
            logger.error(f"Pin {pin} is not configured as output")
            raise ValueError(f"Pin {pin} is not configured as output")
        
        if pin in self._pwm_pins:
            logger.warning(f"PWM for pin {pin} already exists. Using existing PWM.")
        
        HARDWARE_PWM_PINS = [12, 13, 18, 19]
        if pin not in HARDWARE_PWM_PINS:
            logger.warning(f"Pin {pin} is not a hardware PWM pin. Using software PWM instead. For hardware PWM, use pins (12, 13) or (18, 19). (Tuples use same PWM generator)")
        else:
            HW_PWM_PINS = [x for x in HARDWARE_PWM_PINS if x in self._pwm_pins]
            HW_PWM_PINS.append(pin)
            if len([x for x in HW_PWM_PINS if x in [12, 13]]) > 1:
                logger.warning(f"Pin 12 and 13 are sharing same PWM generator. Changing one changes both.")
            elif len([x for x in HW_PWM_PINS if x in [18, 19]]) > 1:
                logger.warning(f"Pin 18 and 19 are sharing hardware PWM pins. Changing one changes both.")

        try:
            pwm_info = HW.pwm(pin, frequency)
            self._pwm_pins[pin] = pwm_info
        except Exception as e:
            logger.error(f"Failed to set up PWM for pin {pin}: {str(e)}")
            raise RuntimeError(f"Failed to set up PWM: {str(e)}")
   
    def set_pwm_duty_cycle(self, pin: int, duty_cycle: float) -> None:
        """
        Set the duty cycle of a PWM pin.
        """
        if pin not in self._pwm_pins:
            logger.error(f"PWM for pin {pin} does not exist")
            raise ValueError(f"PWM for pin {pin} does not exist")

        if duty_cycle < 0 or duty_cycle > 100:
            logger.error(f"Invalid duty cycle: {duty_cycle}")
            raise ValueError(f"Invalid duty cycle: {duty_cycle}")
        
        self._pwm_pins[pin].pwm.ChangeDutyCycle(duty_cycle)
        self._pwm_pins[pin].duty_cycle = duty_cycle
        logger.info(f"Set duty cycle of PWM for pin {pin} to {duty_cycle*100}%")
    
    def get_pwm_pin_info(self, pin: int) -> tuple[int, int, float|None] | None:
        """
        Get the PWM info for a pin.
        Returns a tuple of (pin, frequency, duty_cycle) or None if the pin is sot set up as PWM
        """
        if pin not in self._pwm_pins:
            logger.info(f"Trying to get PWM info for pin {pin}, but it does not exist")
            return None

        return (self._pwm_pins[pin].pin, self._pwm_pins[pin].frequency, self._pwm_pins[pin].duty_cycle)

    def set_pwm_frequency(self, pin: int, frequency: int) -> None:
        """
        Set the frequency of a PWM pin.
        """
        if pin not in self._pwm_pins:
            logger.error(f"PWM for pin {pin} does not exist")
            raise ValueError(f"PWM for pin {pin} does not exist")
        
        self._pwm_pins[pin].pwm.ChangeFrequency(frequency)
        self._pwm_pins[pin].frequency = frequency
        logger.info(f"Set frequency of PWM for pin {pin} to {frequency}Hz")
    
    def start_pwm(self, pin: int, duty_cycle: float = 50) -> None:
        """
        Start the PWM for a pin.
        """
        if pin not in self._pwm_pins:
            logger.error(f"PWM for pin {pin} does not exist")
            raise ValueError(f"PWM for pin {pin} does not exist")
        
        self._pwm_pins[pin].pwm.start(duty_cycle)
        logger.info(f"Started PWM for pin {pin} with duty cycle {duty_cycle}%")
        
    def stop_pwm(self, pin: int) -> None:
        """
        Stop the PWM for a pin.
        """
        if pin not in self._pwm_pins:
            logger.error(f"PWM for pin {pin} does not exist")
            raise ValueError(f"PWM for pin {pin} does not exist")
        
        self._pwm_pins[pin].pwm.stop()
        logger.info(f"Stopped PWM for pin {pin}")

    def remove_pwm(self, pin: int) -> None:
        """
        Remove the PWM for a pin.
        Stops the PWM and removes the pin from the PWM dictionary.
        """
        if pin not in self._pwm_pins:
            logger.error(f"PWM for pin {pin} does not exist")
            return
        self._pwm_pins[pin].pwm.stop()
        del self._pwm_pins[pin]
        logger.info(f"Removed PWM for pin {pin}")
    
    def cleanup(self) -> None:
        """
        Clean up GPIO resources.
        
        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            # Call onClear callbacks for all pins
            for pin, callbacks in self._pin_callbacks.items():
                for callback_info in callbacks:
                    if callback_info.on_clear:
                        try:
                            callback_info.on_clear(pin, self.get_pin_state(pin))
                        except Exception as e:
                            logger.error(f"Error in onClear callback for pin {pin}: {e}")
            
            HW.cleanup()
            self._output_pin_states.clear()
            self._pin_modes.clear()
            self._pin_callbacks.clear()
            [self.remove_pwm(pin) for pin in self._pwm_pins]
            self._pwm_pins.clear()
        except Exception as e:
            raise RuntimeError(f"Cleanup failed: {str(e)}")
        logger.info("GPIO cleanup completed")

# Create the singleton instance
gpio_manager = GPIOManager()

# Export the instance rather than the class
__all__ = ['gpio_manager']

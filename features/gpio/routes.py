"""
GPIO API Routes

This module provides the API endpoints for GPIO control.
"""
from flask import Blueprint, jsonify, request, render_template
from .manager import GPIOManager
from .hardware import GPIO
import threading
import logging
import RPi.GPIO as RPI_GPIO

logger = logging.getLogger(__name__)

# Initialize Blueprint and GPIO manager with thread safety
gpio_bp = Blueprint('gpio', __name__,
                   url_prefix='/gpio',
                   template_folder='../../templates')
gpio_manager = GPIOManager()
gpio_lock = threading.Lock()

@gpio_bp.route('/')
def control():
    """
    Render the GPIO control interface.
    
    Returns:
        Rendered GPIO control template
    """
    return render_template('gpio_control.html')

@gpio_bp.route('/api/pins', methods=['GET'])
def get_gpio_pins():
    """
    Get list of available GPIO pins and their states.
    
    Returns:
        JSON response containing:
        - pins: List of pin objects with number, mode, and state
    """
    with gpio_lock:
        try:
            available_pins = gpio_manager.get_available_pins()
            configured_pins = gpio_manager.get_configured_pins()
            pins = []
            
            for pin in available_pins:
                try:
                    if pin in configured_pins:
                        # Get state for configured pins
                        state = gpio_manager.get_pin_state(pin)
                        pins.append({
                            'number': pin,
                            'mode': configured_pins[pin],
                            'state': state['state'],
                            'configured': True
                        })
                    else:
                        # Return default state for unconfigured pins
                        pins.append({
                            'number': pin,
                            'mode': GPIO.IN,
                            'state': GPIO.LOW,
                            'configured': False
                        })
                except Exception as e:
                    logger.error(f"Error getting state for pin {pin}: {str(e)}")
                    # If error occurs, return unconfigured state
                    pins.append({
                        'number': pin,
                        'mode': GPIO.IN,
                        'state': GPIO.LOW,
                        'configured': False
                    })
            
            return jsonify({
                'status': 'success',
                'pins': pins
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@gpio_bp.route('/api/configure', methods=['POST'])
def configure_gpio():
    """
    Configure GPIO pin mode.
    
    Expected JSON payload:
    {
        "pin": int,  # GPIO pin number
        "mode": str  # "IN" or "OUT"
    }
    
    Returns:
        JSON response with updated pin state
    """
    with gpio_lock:
        try:
            data = request.get_json()
            if not data or 'pin' not in data or 'mode' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields: pin, mode'
                }), 400
                
            pin = data['pin']
            mode = data['mode']
            
            # Configure the pin
            state = gpio_manager.configure_pin(pin, mode)
            
            return jsonify({
                'status': 'success',
                'pin': state
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@gpio_bp.route('/api/state', methods=['POST'])
def set_gpio_state():
    """
    Set GPIO pin state.
    
    Expected JSON payload:
    {
        "pin": int,   # GPIO pin number
        "state": int  # 0 or 1
    }
    
    Returns:
        JSON response with updated pin state
    """
    with gpio_lock:
        try:
            data = request.get_json()
            if not data or 'pin' not in data or 'state' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields: pin, state'
                }), 400
                
            pin = data['pin']
            state = data['state']
            
            # Get current configuration
            configured_pins = gpio_manager.get_configured_pins()
            
            # Verify pin is configured as output
            if pin not in configured_pins:
                return jsonify({
                    'status': 'error',
                    'message': f'Pin {pin} is not configured'
                }), 400
                
            if configured_pins[pin] != GPIO.OUT:
                return jsonify({
                    'status': 'error',
                    'message': f'Pin {pin} is not configured as output'
                }), 400
            
            # Set the state
            new_state = gpio_manager.set_pin_state(pin, state)
            
            return jsonify({
                'status': 'success',
                'pin': new_state
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@gpio_bp.route('/api/cleanup', methods=['POST'])
def cleanup_gpio():
    """
    Clean up GPIO resources.
    
    Returns:
        JSON response indicating success/failure
    """
    with gpio_lock:
        try:
            gpio_manager.cleanup()
            return jsonify({
                'status': 'success',
                'message': 'GPIO cleanup completed'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
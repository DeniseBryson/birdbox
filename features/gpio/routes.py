"""
GPIO API Routes

This module provides the API endpoints for GPIO control.
"""
from flask import Blueprint, jsonify, request, render_template
from .manager import GPIOManager, GPIO
import threading
import logging
from werkzeug.exceptions import BadRequest

# Try to import RPi.GPIO, but don't fail if not available
try:
    import RPi.GPIO as RPI_GPIO
except ImportError:
    RPI_GPIO = None

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
                    pin_data = {
                        'number': pin,
                        'mode': configured_pins.get(pin, GPIO.IN),
                        'configured': pin in configured_pins
                    }
                    
                    if pin_data['configured']:
                        pin_data['state'] = gpio_manager.get_pin_state(pin)
                    else:
                        pin_data['state'] = GPIO.LOW
                        
                    pins.append(pin_data)
                except Exception as e:
                    logger.error(f"Error getting state for pin {pin}: {str(e)}")
                    continue
            
            return jsonify({'pins': pins})
        except Exception as e:
            logger.error(f"Failed to get GPIO pins: {str(e)}")
            return jsonify({'error': str(e)}), 500

@gpio_bp.route('/api/configure', methods=['POST'])
def configure_gpio():
    """
    Configure a GPIO pin's mode.
    
    Expected JSON body:
    {
        "pin": <pin_number>,
        "mode": "IN" or "OUT"
    }
    """
    with gpio_lock:
        try:
            try:
                data = request.get_json()
            except BadRequest:
                return jsonify({'error': 'Invalid JSON format'}), 400
                
            if not data or 'pin' not in data or 'mode' not in data:
                return jsonify({'error': 'Missing required parameters'}), 400
                
            pin = int(data['pin'])
            mode = data['mode']
            
            if pin not in gpio_manager.get_available_pins():
                return jsonify({'error': 'Invalid pin number'}), 400
                
            if mode not in [GPIO.IN, GPIO.OUT]:
                return jsonify({'error': 'Invalid mode'}), 400
                
            gpio_manager.configure_pin(pin, mode)
            return jsonify({
                'status': 'success',
                'pin': pin,
                'mode': mode,
                'state': gpio_manager.get_pin_state(pin)
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Failed to configure GPIO pin: {str(e)}")
            return jsonify({'error': str(e)}), 500

@gpio_bp.route('/api/state', methods=['POST'])
def set_gpio_state():
    """
    Set a GPIO pin's state.
    
    Expected JSON body:
    {
        "pin": <pin_number>,
        "state": 0 or 1
    }
    """
    with gpio_lock:
        try:
            try:
                data = request.get_json()
            except BadRequest:
                return jsonify({'error': 'Invalid JSON format'}), 400
                
            if not data or 'pin' not in data or 'state' not in data:
                return jsonify({'error': 'Missing required parameters'}), 400
                
            pin = int(data['pin'])
            state = int(data['state'])
            
            if pin not in gpio_manager.get_available_pins():
                return jsonify({'error': 'Invalid pin number'}), 400
                
            if state not in [GPIO.LOW, GPIO.HIGH]:
                return jsonify({'error': 'Invalid state value'}), 400
                
            gpio_manager.set_pin_state(pin, state)
            return jsonify({
                'status': 'success',
                'pin': pin,
                'state': state
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except RuntimeError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Failed to set GPIO state: {str(e)}")
            return jsonify({'error': str(e)}), 500

@gpio_bp.route('/api/cleanup', methods=['POST'])
def cleanup_gpio():
    """Clean up GPIO resources."""
    with gpio_lock:
        try:
            gpio_manager.cleanup()
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Failed to clean up GPIO: {str(e)}")
            return jsonify({'error': str(e)}), 500
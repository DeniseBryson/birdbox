"""
GPIO API Routes

This module provides the API endpoints for GPIO control.
"""
from flask import Blueprint, jsonify, request, render_template
from .manager import GPIOManager
from .hardware import GPIO

# Initialize Blueprint and GPIO manager
gpio_bp = Blueprint('gpio', __name__,
                   url_prefix='/gpio',
                   template_folder='../../templates')  # Path relative to this file
gpio_manager = GPIOManager()

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
    try:
        available_pins = gpio_manager.get_available_pins()
        pins = []
        for pin in available_pins:
            try:
                state = gpio_manager.get_pin_state(pin)
                pins.append({
                    'number': pin,
                    'mode': state['mode'],
                    'state': state['state'],
                    'configured': state.get('configured', True)
                })
            except RuntimeError:
                # Include unconfigured pins with default state
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
    try:
        try:
            data = request.get_json()
        except Exception:
            return jsonify({
                'status': 'error',
                'message': 'Invalid JSON'
            }), 400
            
        if not data or 'pin' not in data or 'mode' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: pin, mode'
            }), 400
            
        try:
            pin = int(data['pin'])
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid pin number format'
            }), 400
            
        mode = data['mode'].upper()
        if mode not in [GPIO.IN, GPIO.OUT]:
            return jsonify({
                'status': 'error',
                'message': f'Invalid mode: {mode}'
            }), 400
            
        if pin not in GPIO.VALID_PINS:
            return jsonify({
                'status': 'error',
                'message': f'Invalid GPIO pin: {pin}'
            }), 400
            
        state = gpio_manager.configure_pin(pin, mode)
        return jsonify({
            'status': 'success',
            'pin': pin,
            'mode': mode
        })
    except RuntimeError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@gpio_bp.route('/api/state', methods=['POST'])
def set_gpio_state():
    """
    Set GPIO pin state (for output pins).
    
    Expected JSON payload:
    {
        "pin": int,  # GPIO pin number
        "state": int  # 0 or 1
    }
    
    Returns:
        JSON response with updated pin state
    """
    try:
        try:
            data = request.get_json()
        except Exception:
            return jsonify({
                'status': 'error',
                'message': 'Invalid JSON'
            }), 400
            
        if not data or 'pin' not in data or 'state' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: pin, state'
            }), 400
            
        try:
            pin = int(data['pin'])
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid pin number format'
            }), 400
            
        try:
            state = int(data['state'])
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid state value'
            }), 400
            
        if state not in [GPIO.LOW, GPIO.HIGH]:
            return jsonify({
                'status': 'error',
                'message': 'Invalid state value'
            }), 400
            
        if pin not in GPIO.VALID_PINS:
            return jsonify({
                'status': 'error',
                'message': f'Invalid GPIO pin: {pin}'
            }), 400
            
        # First check if pin is configured
        try:
            new_state = gpio_manager.set_pin_state(pin, state)
            return jsonify({
                'status': 'success',
                'pin': pin,
                'state': state
            })
        except RuntimeError as e:
            if "Pin not configured" in str(e):
                return jsonify({
                    'status': 'error',
                    'message': 'Pin not configured'
                }), 400
            raise
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
            
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
        JSON response indicating success
    """
    try:
        gpio_manager.cleanup()
        return jsonify({
            'status': 'success',
            'message': 'GPIO cleanup completed'
        })
    except RuntimeError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
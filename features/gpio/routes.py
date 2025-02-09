"""
GPIO API Routes

This module provides the API endpoints for GPIO control.
"""
import asyncio
import json
from typing import Any
from flask import Blueprint, jsonify, request, render_template 
from flask_sock import Sock
from .manager import GPIOManager
from .hardware import HIGH, LOW, IN, OUT, UNDEFINED
import threading
import logging
from werkzeug.exceptions import BadRequest


logger = logging.getLogger(__name__)

# Initialize Blueprint, WebSocket, and GPIO manager with thread safety
gpio_bp = Blueprint('gpio', __name__,
                   url_prefix='/gpio',
                   template_folder='../../templates')
sock = Sock()
gpio_manager = GPIOManager()
gpio_lock = threading.Lock()

# Track active WebSocket connections
active_connections: set[Sock] = set()

def pin_state_changed(pin: int, state: int):
    """Callback for GPIO pin state changes."""
    message = json.dumps({
        'type': 'gpio_update',
        'data': {
            'pin': pin,
            'state': state
        }
    })
    logger.info(f"Pin state changed: {pin} to {state}")
    
    # Broadcast to all active connections
    dead_connections: set[Sock] = set()
    for ws in active_connections:
        try:
            ws.send(message)
        except Exception as e:
            logger.error(f"Failed to send update to websocket: {e}")
            dead_connections.add(ws)
    # Clean up dead connections
    active_connections.difference_update(dead_connections)

@gpio_bp.route('/')
def control():
    """
    Render the GPIO control interface.
    
    Returns:
        Rendered GPIO control template
    """
    return render_template('gpio_control.html')


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
                logger.error("Invalid JSON format")
                return jsonify({'error': 'Invalid JSON format'}), 400
                
            if not data or 'pin' not in data or 'mode' not in data:
                logger.error("Missing required parameters")
                return jsonify({'error': 'Missing required parameters'}), 400
                
            pin = int(data['pin'])
            mode = data['mode']
            
            if pin not in gpio_manager.get_available_pins():
                logger.error(f"Invalid pin number: {pin}")
                return jsonify({'error': 'Invalid pin number'}), 400
                
            if mode not in [IN, OUT]:
                logger.error(f"Invalid mode: {mode}")
                return jsonify({'error': 'Invalid mode'}), 400
                

            gpio_manager.configure_pin(
                pin, 
                mode, 
                callback=lambda p, state: pin_state_changed(p, state)
            )
            logger.info(f"Configured pin {pin} as {mode}")

            return jsonify({
                'status': 'success',
                'pin': pin,
                'mode': mode,
                'state': gpio_manager.get_pin_state(pin)
            })
        except ValueError as e:
            logger.error(f"Failed to configure GPIO pin: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Failed to configure GPIO pin: {str(e)}")
            return jsonify({'error': str(e)}), 500

@sock.route('/ws/gpio-updates')
async def gpio_updates(ws: Sock):
    """
    WebSocket endpoint for real-time GPIO updates.
    
    Sends GPIO state updates to connected clients in real-time using callbacks
    for input pins and periodic updates for output pins.
    """
    try:
        # Add this connection to active set
        active_connections.add(ws)
        logger.info(f"New WebSocket connection. Active connections: {len(active_connections)}")
        
        # Send complete initial state
        with gpio_lock:
            pins = gpio_manager.get_available_pins()
            configured_pins = gpio_manager.get_configured_pins()
            states = {
                pin: gpio_manager.get_pin_state(pin) 
                for pin in pins 
                if pin in configured_pins
            }

            logger.info(f"Sending initial state to client: {states}")
            ws.send(json.dumps({
                'type': 'gpio_update',
                'data': {
                    'pins': pins,
                    'states': states,
                }
            }))
           
        # Keep connection alive
        while True:
            try:
                ws.send("ping")
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Failed to send ping: {e}")
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Remove from active connections and clean up callbacks
        active_connections.remove(ws)
        logger.debug(f"Removed connection, active connections left: {len(active_connections)}")
        
        if len(active_connections) == 0:
            # If this was the last connection, remove all callbacks
            with gpio_lock:
                configured_pins = gpio_manager.get_configured_pins()
                for pin, mode in configured_pins.items():
                    if mode in [IN, OUT]:
                        logger.debug(f"Removing callback for pin {pin}")
                        gpio_manager.configure_pin(pin, mode, callback=None)
                    else:
                        logger.debug(f"Pin {pin} mode {mode} not in [IN, OUT], skipping callback removal")
        
        try:
            ws.close()
        except Exception as e:
            logger.error(f"Error closing websocket: {e}")

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
            pins: list[dict[str, Any]] = []
            
            for pin in available_pins:
                pin_data = {
                    'number': pin,
                    'configured': pin in configured_pins,
                    'mode': configured_pins.get(pin, UNDEFINED),
                    'state': UNDEFINED  # Default state for unconfigured pins
                }
                
                # Only try to get state if pin is configured
                if pin in configured_pins:
                    try:
                        pin_data['state'] = gpio_manager.get_pin_state(pin)
                    except Exception as e:
                        logger.debug(f"Could not get state for configured pin {pin}: {str(e)}")
                        # Keep default state
                
                pins.append(pin_data)
            
            return jsonify({'pins': pins})
        except Exception as e:
            logger.error(f"Failed to get GPIO pins: {str(e)}")
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
            state = data['state']
            
            if pin not in gpio_manager.get_available_pins():
                return jsonify({'error': 'Invalid pin number'}), 400
                
            if state not in [LOW, HIGH]:
                return jsonify({'error': 'Invalid state value'}), 400
            
            # Check if pin is configured as output before setting state
            configured_pins = gpio_manager.get_configured_pins()
            if pin not in configured_pins:
                return jsonify({'error': f'Pin {pin} is not configured'}), 400
            
            if configured_pins[pin] != OUT:
                return jsonify({'error': f'Pin {pin} is configured as input and cannot have its state set'}), 400
                
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
    
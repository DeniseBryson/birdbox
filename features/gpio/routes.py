"""
GPIO API Routes

This module provides the API endpoints for GPIO control.
"""
import json
from operator import indexOf
from typing import Any
from uuid import uuid4
from flask import Blueprint, jsonify, request, render_template 
from flask_sock import Sock # type: ignore


from features.gpio.constants import PinMode
from .manager import gpio_manager
from .hardware import HIGH, LOW, IN, OUT
import threading
import logging
from werkzeug.exceptions import BadRequest


logger = logging.getLogger(__name__)

# Initialize Blueprint, WebSocket, and GPIO manager with thread safety
gpio_bp = Blueprint('gpio', __name__,
                   url_prefix='/gpio',
                   template_folder='../../templates')
sock: Sock = Sock()
gpio_lock = threading.Lock()

# Track active WebSocket connections
active_connections: dict[str, Sock] = {}
stop_signals: dict[str, threading.Event] = {}

def pin_state_changed(pin: int, state: int):
    """Callback for GPIO pin state changes."""
    message = json.dumps({
        'type': 'gpio_pin_update',
        'data': {
            'pin': pin,
            'state': state
        }
    })
    
    # Broadcast to all active connections
    dead_connections: list[str] = []
    for ws_id, ws in active_connections.items():
        try:
            logger.info(f"Sending pin change message to websocket {ws_id}: {message}")
            ws.send(message) # type: ignore
        except Exception as e:
            logger.error(f"Failed to send update to websocket {indexOf(active_connections, ws)}: {e}")
            dead_connections.append(ws_id)
    # Clean up dead connections
    for ws_id in dead_connections:
        cleanup_ws(ws_id)

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
            
            if pin not in gpio_manager.get_valid_pins():
                logger.error(f"Invalid pin number: {pin}")
                return jsonify({'error': 'Invalid pin number'}), 400
                
            if mode not in [IN, OUT, 'IN', 'OUT']:
                logger.error(f"Invalid mode: {mode}")
                return jsonify({'error': 'Invalid mode'}), 400
            
            if mode in ['IN', 'OUT']:
                mode = IN if mode == 'IN' else OUT

            gpio_manager.configure_pin(
                pin, 
                mode, 
                callback=lambda p, state: pin_state_changed(p, state)
            )
            logger.info(f"Configured pin {pin} as {mode}")
            
            configured_pins: dict[int, PinMode] = gpio_manager.get_configured_pins()
            configured_pin: PinMode | None = configured_pins.get(pin, None)

            return jsonify({
                'status': 'success',
                'number': pin,
                'mode': 'OUT' if configured_pin == OUT else 'IN' if configured_pin == IN else 'UNDEFINED',
                'state': gpio_manager.get_pin_state(pin)
            })
        except ValueError as e:
            logger.error(f"Failed to configure GPIO pin: {str(e)}")
            return jsonify({'status': 'error', 'errorMsg': str(e)}), 400
        except Exception as e:
            logger.error(f"Failed to configure GPIO pin: {str(e)}")
            return jsonify({'status': 'error', 'errorMsg': str(e)}), 500

def get_gpios_summary_update_message() -> dict[str, Any]:
    """
    Get the current state of all GPIO pins.
    """
    pins: list[int] = gpio_manager.get_valid_pins()
    configured_pins: dict[int, PinMode] = gpio_manager.get_configured_pins()
    modes: list[int] = [configured_pins.get(pin, -1) for pin in pins]
    messageModes: list[str] = [
        'HIGH'if mode == 1 else 'LOW'if mode ==0 else 'UNDEFINED'
        for mode in modes
    ]
    states: list[dict[str, Any]] = [
        {
            'number': pin,
            'mode': mode,
            'state': gpio_manager.get_pin_state(pin) 
        }
        for pin, mode in zip(pins, messageModes) 
        
    ]
    
    message: dict[str, Any] = {
        'type': 'gpio_update',
        'data': {
            'pins': states,
        }
    }
    return message

def keep_alive(ws_id: str):
    """Keep the connection alive by sending a ping every 60 seconds."""
    
    stop_signal = stop_signals.get(ws_id, None)
    if stop_signal is None or stop_signal.is_set():
        if stop_signal is None:
            logger.error(f"No stop signal found for ws_id {ws_id}, skipping keep-alive")
        else:
            logger.debug(f"Stop signal set for ws_id {ws_id}, skipping keep-alive")
        return
    
    timer = threading.Timer(10.0, keep_alive, [ws_id])
    try:
        ws = active_connections[ws_id]
        logger.debug(f"Sending ping to WebSocket {ws_id}")
        data: dict[str, Any] = {'type': 'ping', 'data': {}}
        ws.send(json.dumps(data)) # type: ignore
        timer.start()
    except Exception as e:
        logger.error(f"Failed to send ping to ws {ws_id}: {e}")
        timer.cancel()
        cleanup_ws(ws_id)

def cleanup_ws(ws_id: str):
    # Remove from active connections and clean up callbacks
    ws = active_connections.pop(ws_id, None)    
    if ws == None:
        logger.error(f"No connection found for ws_id {ws_id} to cleanup")
        return
    
    stop_signal = stop_signals.pop(ws_id, None)
    # Stop the keep-alive thread
    if stop_signal is None:
        logger.error(f"No stop signal found for ws_id {ws_id} to cleanup")
    else: 
        stop_signal.set()  # Signal the thread to stop
        logger.debug(f"Stopped keep-alive thread for ws {ws_id}")

    logger.debug(f"Removed connection {ws_id}, active connections left: {len(active_connections)}")
    if len(active_connections) == 0:
        # If this was the last connection, remove all callbacks
        with gpio_lock:
            configured_pins = gpio_manager.get_configured_pins()
            for pin, mode in configured_pins.items():
                if mode in [IN, OUT]:
                    logger.debug(f"Since last connection closed, removing callback for pin {pin}")
                    gpio_manager.configure_pin(pin, mode, callback=None)
                else:
                    logger.debug(f"Pin {pin} mode {mode} not in [IN, OUT], skipping callback removal")
    try:
        if not ws.connected: # type: ignore
            logger.debug(f"WebSocket {ws_id} is not connected, skipping close")
        else:
            ws.close() # type: ignore    
    except Exception as e:
        logger.error(f"Error closing websocket {ws_id}: {e}")

@sock.route('/ws/gpio-updates') # type: ignore
def gpio_updates(ws: Sock):
    """
    WebSocket endpoint for real-time GPIO updates.
    
    Sends GPIO state updates to connected clients in real-time using callbacks
    for input pins and periodic updates for output pins.
    """
    ws_id = str(uuid4())
    stop_signal = threading.Event()

    try:
        # Add this connection to active set
        active_connections[ws_id] = ws
        stop_signals[ws_id] = stop_signal
        logger.info(f"New WebSocket connection. Active connections: {len(active_connections)}")
        
        # Send complete initial state
        with gpio_lock:
            message = get_gpios_summary_update_message()
            #logger.info(f"Sending initial state to ws {indexOf(active_connections, ws)}")
            ws.send(json.dumps(message)) # type: ignore

        # Start keep-alive in a separate thread
        thread = threading.Thread(target=keep_alive, kwargs={'ws_id': ws_id}, daemon=True)
        logger.debug(f"Started keep-alive thread for ws {ws_id}")
        thread.start()    

        # Handle incoming messages if needed
        while ws.connected: # type: ignore
            message = ws.receive() # type: ignore # Blocks until a message is received 
            if message is None:
                break  # Client disconnected
            logger.debug(f"Received message from ws {ws_id}: {message}, doing nothing with it")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        cleanup_ws(ws_id)

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
            message = get_gpios_summary_update_message()
            return jsonify({'pins': message['data']['pins']})
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
        "state": <PinState>
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
            
            if pin not in gpio_manager.get_valid_pins():
                return jsonify({'error': 'Invalid pin number'}), 400
                
            if state not in [LOW, HIGH, 'LOW', 'HIGH']:
                return jsonify({'error': 'Invalid state value'}), 400
            
            if state == 'LOW':
                state = LOW
            elif state == 'HIGH':
                state = HIGH
            
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
    
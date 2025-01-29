"""
WebSocket handler for real-time GPIO updates.
"""
import json
import asyncio
from flask_sock import Sock
from .manager import GPIOManager, GPIO
import threading

# Initialize WebSocket and GPIO manager
sock = Sock()
gpio_manager = GPIOManager()
gpio_lock = threading.Lock()

# Track active WebSocket connections
active_connections = set()

def pin_state_changed(pin):
    """Callback for GPIO pin state changes."""
    state = gpio_manager.get_pin_state(pin)
    message = json.dumps({
        'type': 'gpio_update',
        'data': {
            'pin': pin,
            'state': state
        }
    })
    # Broadcast to all active connections
    dead_connections = set()
    for ws in active_connections:
        try:
            ws.send(message)
        except Exception:
            dead_connections.add(ws)
    # Clean up dead connections
    active_connections.difference_update(dead_connections)

@sock.route('/ws/gpio-updates')
def gpio_updates(ws):
    """
    WebSocket endpoint for real-time GPIO updates.
    
    Sends GPIO state updates to connected clients in real-time using callbacks
    for input pins and periodic updates for output pins.
    """
    try:
        # Add this connection to active set
        active_connections.add(ws)
        
        # Configure callbacks for all input pins
        with gpio_lock:
            pins = gpio_manager.get_available_pins()
            for pin in pins:
                if gpio_manager._pin_modes.get(pin) == GPIO.IN:
                    gpio_manager.configure_pin(pin, GPIO.IN, callback=lambda channel, p=pin: pin_state_changed(p))
        
        # Send initial states
        pins = gpio_manager.get_available_pins()
        states = {pin: gpio_manager.get_pin_state(pin) for pin in pins}
        ws.send(json.dumps({
            'type': 'gpio_update',
            'data': {
                'pins': pins,
                'states': states
            }
        }))
        
        # Keep connection alive and periodically update output pin states
        while True:
            # Only send updates for output pins periodically
            output_states = {}
            for pin in pins:
                if gpio_manager._pin_modes.get(pin) == GPIO.OUT:
                    output_states[pin] = gpio_manager.get_pin_state(pin)
            
            if output_states:
                ws.send(json.dumps({
                    'type': 'gpio_update',
                    'data': {
                        'states': output_states
                    }
                }))
            
            # Wait before next output pin update
            asyncio.sleep(1)
            
    except Exception as e:
        # Log error and clean up
        print(f"WebSocket error: {str(e)}")
    finally:
        # Remove from active connections and clean up callbacks
        active_connections.remove(ws)
        if len(active_connections) == 0:
            # If this was the last connection, remove all callbacks
            with gpio_lock:
                for pin in gpio_manager.get_available_pins():
                    if gpio_manager._pin_modes.get(pin) == GPIO.IN:
                        gpio_manager.configure_pin(pin, GPIO.IN)  # Removes callback
        ws.close() 
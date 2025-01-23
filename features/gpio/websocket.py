"""
WebSocket handler for real-time GPIO updates.
"""
import json
import asyncio
from flask_sock import Sock
from .manager import GPIOManager

# Initialize WebSocket and GPIO manager
sock = Sock()
gpio_manager = GPIOManager()

@sock.route('/ws/gpio-updates')
def gpio_updates(ws):
    """
    WebSocket endpoint for real-time GPIO updates.
    
    Sends GPIO state updates to connected clients every second.
    Message format:
    {
        "type": "gpio_update",
        "data": {
            "pins": [...],
            "states": {...}
        }
    }
    """
    try:
        while True:
            # Get current GPIO states
            pins = gpio_manager.get_available_pins()
            states = {pin: gpio_manager.get_pin_state(pin) for pin in pins}
            
            # Send update
            ws.send(json.dumps({
                'type': 'gpio_update',
                'data': {
                    'pins': pins,
                    'states': states
                }
            }))
            
            # Wait before next update
            asyncio.sleep(1)
    except Exception as e:
        # Log error and close connection
        print(f"WebSocket error: {str(e)}")
        ws.close() 
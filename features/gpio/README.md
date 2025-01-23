# GPIO Control Feature

This feature provides comprehensive GPIO (General Purpose Input/Output) control functionality for the BirdsOS project, with support for both real Raspberry Pi hardware and development environments.

## Features

- Hardware abstraction layer for GPIO control
- Real-time pin state monitoring
- Input/Output mode configuration
- Pin state toggling for output pins
- Mock implementation for development
- WebSocket-based real-time updates
- Comprehensive test coverage

## Quick Start

1. Import and register the GPIO blueprints in your Flask app:

```python
from features.gpio import gpio_bp, sock

app.register_blueprint(gpio_bp)
sock.init_app(app)
```

2. Access the GPIO control interface at `/gpio`

## API Endpoints

### Get Available Pins
```http
GET /api/gpio/pins

Response:
{
    "status": "success",
    "pins": [2, 3, 4, ...],
    "states": {
        "2": {
            "pin": 2,
            "mode": "IN",
            "state": 0,
            "name": "GPIO2"
        },
        ...
    }
}
```

### Configure Pin Mode
```http
POST /api/gpio/configure
Content-Type: application/json

{
    "pin": 2,
    "mode": "OUT"  // "IN" or "OUT"
}

Response:
{
    "status": "success",
    "state": {
        "pin": 2,
        "mode": "OUT",
        "state": 0,
        "name": "GPIO2"
    }
}
```

### Set Pin State
```http
POST /api/gpio/state
Content-Type: application/json

{
    "pin": 2,
    "state": 1  // 0 or 1
}

Response:
{
    "status": "success",
    "state": {
        "pin": 2,
        "mode": "OUT",
        "state": 1,
        "name": "GPIO2"
    }
}
```

### Cleanup GPIO Resources
```http
POST /api/gpio/cleanup

Response:
{
    "status": "success",
    "message": "GPIO cleanup completed"
}
```

## WebSocket Updates

Connect to `/ws/gpio-updates` for real-time GPIO state updates:

```javascript
const ws = new WebSocket('ws://' + location.host + '/ws/gpio-updates');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'gpio_update') {
        // Handle pin states update
        console.log(data.data.states);
    }
};
```

## Development

### Running Tests

```bash
pytest features/gpio/tests/
```

### Mock Implementation

The feature automatically detects if it's running on a Raspberry Pi. If not, it uses a mock implementation that simulates GPIO behavior, perfect for development and testing.

### Adding New GPIO Features

1. Implement the feature in `manager.py`
2. Add corresponding API endpoints in `routes.py`
3. Add tests in `tests/`
4. Update the UI in `templates/gpio_control.html`

## Example Usage

### Python Code
```python
from features.gpio import GPIOManager

# Initialize GPIO manager
gpio = GPIOManager()

# Configure pin as output
gpio.configure_pin(18, 'OUT')

# Set pin high
gpio.set_pin_state(18, 1)

# Get pin state
state = gpio.get_pin_state(18)
print(f"Pin 18 is {'HIGH' if state['state'] else 'LOW'}")

# Cleanup when done
gpio.cleanup()
```

### JavaScript Code
```javascript
// Initialize GPIO controller
const controller = new GPIOController();

// Configure pin as output
await controller.configurePin(18, 'OUT');

// Toggle pin state
await controller.togglePinState(18, 1);
```

## Security Considerations

1. Pin access is restricted to valid GPIO pins only
2. Input validation for all API endpoints
3. Error handling for hardware failures
4. Automatic cleanup on application shutdown

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Add tests for your changes
5. Submit a pull request

## License

This feature is part of the BirdsOS project and is licensed under the same terms.

## Test Coverage TODO

### UI Tests
- [ ] Test pin selection dropdown population
- [ ] Test mode switching (Input/Output)
- [ ] Test pin state indicators
- [ ] Test pin overview table updates
- [ ] Test toggle button functionality
- [ ] Test real-time updates
- [ ] Test mobile responsiveness
- [ ] Test browser compatibility (Chrome, Firefox, Safari)
- [ ] Test concurrent user interactions
- [ ] Test UI state consistency with backend
- [ ] Test UI behavior during network latency

### Error Handling Tests
- [ ] Test concurrent access to same GPIO pin
- [ ] Test hardware access failures
- [ ] Test application shutdown cleanup
- [ ] Test WebSocket connection drops
- [ ] Test invalid API responses
- [ ] Test error message display in UI
- [ ] Test recovery after errors
- [ ] Test rate limiting behavior
- [ ] Test timeout handling
- [ ] Test invalid state transitions

### Performance Tests
- [ ] Test response time under load
- [ ] Test WebSocket update frequency
- [ ] Test memory usage with multiple clients
- [ ] Test WebSocket client cleanup
- [ ] Test UI performance with many pins
- [ ] Test rapid state changes
- [ ] Test concurrent API requests
- [ ] Test data throughput limits
- [ ] Test browser resource usage
- [ ] Test backend resource usage

### Integration Tests
- [ ] Test GPIO and motor control interaction
- [ ] Test state persistence across restarts
- [ ] Test mock/real hardware switching
- [ ] Test rapid mode switching
- [ ] Test with other system components
- [ ] Test startup sequence
- [ ] Test shutdown sequence
- [ ] Test system state recovery
- [ ] Test configuration changes
- [ ] Test logging integration

### Security Tests
- [ ] Test access control for endpoints
- [ ] Test input sanitization
- [ ] Test WebSocket authentication
- [ ] Test API rate limiting
- [ ] Test permission levels
- [ ] Test data validation
- [ ] Test error exposure
- [ ] Test secure connections
- [ ] Test session handling
- [ ] Test audit logging

### Edge Cases
- [ ] Test boundary values for pin numbers
- [ ] Test maximum WebSocket connections
- [ ] Test invalid JSON payloads
- [ ] Test unicode input
- [ ] Test large data payloads
- [ ] Test rapid connection/disconnection
- [ ] Test browser tab switching
- [ ] Test system resource limits
- [ ] Test error condition combinations
- [ ] Test recovery scenarios 
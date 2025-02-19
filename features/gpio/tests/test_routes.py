# pyright: reportPrivateUsage=false
"""
Test suite for GPIO routes
"""
import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask
from flask_sock import Sock # type: ignore
from flask.testing import FlaskClient
from ..routes import gpio_bp, gpio_manager, active_connections
from ..hardware import (
     HIGH, LOW, IN, OUT, UNDEFINED,
    PUD_OFF, PUD_UP, PUD_DOWN, BOTH, BCM
)

@pytest.fixture
def app():
    """Create test Flask application"""
    app = Flask(__name__)
    app.register_blueprint(gpio_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client"""
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_state():
    """Reset GPIO manager and active connections between tests"""
    active_connections.clear()
    gpio_manager._pin_modes.clear()
    gpio_manager._output_pin_states.clear()
    gpio_manager._output_pin_callbacks.clear()
    yield

@pytest.fixture
def mock_hardware():
    """Mock hardware interface"""
    with patch('features.gpio.manager.HW') as mock:
        # Set up GPIO constants
        mock.HIGH = HIGH
        mock.LOW = LOW
        mock.IN = IN
        mock.OUT = OUT
        mock.UNDEFINED = UNDEFINED
        mock.PUD_OFF = PUD_OFF
        mock.PUD_UP = PUD_UP
        mock.PUD_DOWN = PUD_DOWN
        mock.BOTH = BOTH
        mock.BCM = BCM
        # Set up valid pins
        mock.get_valid_pins.return_value = [18, 23, 24]
        # Make get_pin_state return actual values instead of mocks
        mock.get_pin_state.return_value = LOW
        yield mock

class TestGPIORoutes:
    
    def test_control_page(self, client: FlaskClient):
        """Test GPIO control page renders"""
        response = client.get('/gpio/')
        assert response.status_code == 200
        assert b'html' in response.data
        assert b'GPIO Control' in response.data
        assert b'GPIO Pins' in response.data
        assert b'GPIO State' in response.data
        assert b'GPIO Mode' in response.data
        assert b'GPIO Cleanup' in response.data
        assert b'WebSocket' in response.data
        assert b'GPIO Updates' in response.data
        

    def test_configure_pin_input(self, client: FlaskClient, mock_hardware: Mock):
        """Test configuring a pin as input"""
        response = client.post('/gpio/api/configure', 
                             json={'pin': 18, 'mode': IN})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['pin'] == 18
        assert data['mode'] == IN
        
        # Verify hardware calls
        mock_hardware.setup_input_pin.assert_called_once()
        assert gpio_manager._pin_modes[18] == IN

    def test_configure_pin_output(self, client: FlaskClient, mock_hardware: Mock):
        """Test configuring a pin as output"""
        response = client.post('/gpio/api/configure', 
                             json={'pin': 18, 'mode': OUT})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['pin'] == 18
        assert data['mode'] == OUT
        
        # Verify hardware calls
        mock_hardware.setup_output_pin.assert_called_once()
        assert gpio_manager._pin_modes[18] == OUT
        assert gpio_manager._output_pin_states[18] == HIGH

    def test_configure_pin_invalid_pin(self, client: FlaskClient, mock_hardware: Mock):
        """Test configuring an invalid pin"""
        response = client.post('/gpio/api/configure', 
                             json={'pin': 999, 'mode': IN})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid pin number' in data['error']

    def test_configure_pin_invalid_mode(self, client: FlaskClient):
        """Test configuring pin with invalid mode"""
        response = client.post('/gpio/api/configure', 
                             json={'pin': 18, 'mode': 'INVALID'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid mode' in data['error']

    def test_get_pins(self, client: FlaskClient, mock_hardware: Mock):
        """Test getting pin states"""
        # Configure some pins first
        gpio_manager._pin_modes[18] = IN
        gpio_manager._pin_modes[23] = OUT
        gpio_manager._output_pin_states[23] = HIGH
        
        mock_hardware.get_pin_state.return_value = LOW
        
        response = client.get('/gpio/api/pins')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'pins' in data
        pins = {pin['number']: pin for pin in data['pins']}
        
        # Check input pin
        assert pins[18]['configured'] is True
        assert pins[18]['mode'] == IN
        assert pins[18]['state'] == LOW
        
        # Check output pin
        assert pins[23]['configured'] is True
        assert pins[23]['mode'] == OUT
        assert pins[23]['state'] == HIGH
        
        # Check unconfigured pin
        assert pins[24]['configured'] is False
        assert pins[24]['mode'] == UNDEFINED
        assert pins[24]['state'] == UNDEFINED

    def test_set_pin_state(self, client: FlaskClient, mock_hardware: Mock):
        """Test setting pin state"""
        # Configure pin as output first
        gpio_manager._pin_modes[18] = OUT
        
        response = client.post('/gpio/api/state',
                             json={'pin': 18, 'state': HIGH})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['pin'] == 18
        assert data['state'] == HIGH
        
        # Verify hardware calls
        mock_hardware.set_output_state.assert_called_once_with(18, HIGH)
        assert gpio_manager._output_pin_states[18] == HIGH

    def test_set_pin_state_input_pin(self, client: FlaskClient):
        """Test setting state of input pin fails"""
        # Configure pin as input
        gpio_manager._pin_modes[18] = IN
        
        response = client.post('/gpio/api/state',
                             json={'pin': 18, 'state': HIGH})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'configured as input' in data['error']

    def test_set_pin_state_unconfigured(self, client: FlaskClient):
        """Test setting state of unconfigured pin fails"""
        response = client.post('/gpio/api/state',
                             json={'pin': 18, 'state': HIGH})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not configured' in data['error']

    def test_cleanup(self, client: FlaskClient, mock_hardware: Mock):
        """Test GPIO cleanup"""
        # Set up some state
        gpio_manager._pin_modes[18] = OUT
        gpio_manager._output_pin_states[18] = HIGH
        
        response = client.post('/gpio/api/cleanup')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        # Verify cleanup
        mock_hardware.cleanup.assert_called_once()
        assert not gpio_manager._pin_modes
        assert not gpio_manager._output_pin_states

class TestWebSocket:
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, app: Flask, mock_hardware: Mock):
        """Test WebSocket connection and initial state"""
        test_client = app.test_client()
        async with test_client.websocket('/gpio/ws/gpio-updates') as ws:  # type: ignore
            # Configure a pin
            gpio_manager._pin_modes[18] = OUT
            gpio_manager._output_pin_states[18] = HIGH
            
            # Should receive initial state
            msg = await ws.receive()
            data = json.loads(msg)
            
            assert data['type'] == 'gpio_update'
            assert 18 in data['data']['pins']
            assert data['data']['states'][18] == HIGH
            
            # Should be in active connections
            assert ws in active_connections

    @pytest.mark.asyncio
    async def test_websocket_pin_updates(self, app: Flask, mock_hardware: Mock):
        """Test WebSocket receives pin updates"""
        test_client = app.test_client()
        async with test_client.websocket('/gpio/ws/gpio-updates') as ws:  # type: ignore
            # Configure pin with callback
            gpio_manager._pin_modes[18] = IN
            
            # Simulate pin state change
            gpio_manager.configure_pin(18, IN, callback=None)  # Clear any existing callback
            mock_hardware.get_pin_state.return_value = HIGH
            
            # Should receive update
            msg = await ws.receive()
            data = json.loads(msg)
            
            assert data['type'] == 'gpio_update'
            assert data['data']['pin'] == 18
            assert data['data']['state'] == HIGH

    @pytest.mark.asyncio
    async def test_websocket_cleanup(self, app: Flask, mock_hardware: Mock):
        """Test WebSocket cleanup on disconnect"""
        test_client = app.test_client()
        async with test_client.websocket('/gpio/ws/gpio-updates') as ws:  # type: ignore
            # Configure pin
            gpio_manager._pin_modes[18] = IN
            
        # After disconnect
        assert ws not in active_connections
        # Should have cleaned up callbacks
        assert not gpio_manager._output_pin_callbacks 
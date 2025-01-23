"""
Tests for GPIO API Routes
"""
import pytest
import json
from flask import Flask, url_for
from ..routes import gpio_bp

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.register_blueprint(gpio_bp)
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

def test_get_gpio_pins(client):
    """Test getting GPIO pins and states."""
    response = client.get('/gpio/api/pins')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'pins' in data
    assert isinstance(data['pins'], list)
    assert len(data['pins']) > 0
    
    # Check pin data structure
    pin = data['pins'][0]
    assert 'number' in pin
    assert 'mode' in pin
    assert 'state' in pin

def test_configure_gpio(client):
    """Test configuring GPIO pin mode."""
    # Get available pins first
    response = client.get('/gpio/api/pins')
    data = json.loads(response.data)
    pin = data['pins'][0]['number']
    
    # Configure pin as output
    response = client.post('/gpio/api/configure', json={
        'pin': pin,
        'mode': 'OUT'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == pin
    assert data['mode'] == 'OUT'
    
    # Configure pin as input
    response = client.post('/gpio/api/configure', json={
        'pin': pin,
        'mode': 'IN'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == pin
    assert data['mode'] == 'IN'

def test_set_gpio_state(client):
    """Test setting GPIO pin state."""
    # Get available pins first
    response = client.get('/gpio/api/pins')
    data = json.loads(response.data)
    pin = data['pins'][0]['number']
    
    # Configure pin as output
    client.post('/gpio/api/configure', json={
        'pin': pin,
        'mode': 'OUT'
    })
    
    # Set state to HIGH
    response = client.post('/gpio/api/state', json={
        'pin': pin,
        'state': 1
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == pin
    assert data['state'] == 1
    
    # Set state to LOW
    response = client.post('/gpio/api/state', json={
        'pin': pin,
        'state': 0
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == pin
    assert data['state'] == 0

def test_cleanup_gpio(client):
    """Test GPIO cleanup endpoint."""
    response = client.post('/gpio/api/cleanup')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success' 
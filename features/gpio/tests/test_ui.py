"""
UI Tests for GPIO Functionality
"""
import pytest
import json
from flask import url_for
from flask.testing import FlaskClient
from features.gpio.hardware import GPIO
from features.gpio.manager import GPIOManager

@pytest.fixture(autouse=True)
def reset_gpio_manager():
    """Reset GPIO manager singleton state before each test."""
    GPIOManager._instance = None
    GPIOManager._initialized = False
    yield

@pytest.fixture
def client(app) -> FlaskClient:
    """Create a test client."""
    return app.test_client()

def test_gpio_page_load(client):
    """Test that the GPIO control page loads correctly."""
    response = client.get('/gpio/')
    assert response.status_code == 200
    assert b"GPIO Control" in response.data
    assert b"gpio-pin-select" in response.data
    assert b"set-input" in response.data
    assert b"set-output" in response.data
    assert b"gpio-overview" in response.data

def test_gpio_api_pins(client):
    """Test getting GPIO pin information."""
    response = client.get('/gpio/api/pins')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'pins' in data
    pins = data['pins']
    assert isinstance(pins, list)
    assert len(pins) > 0
    
    # Check pin data structure
    pin = pins[0]
    assert 'number' in pin
    assert 'mode' in pin
    assert 'state' in pin
    assert 'configured' in pin
    assert isinstance(pin['number'], int)
    assert pin['mode'] in [GPIO.IN, GPIO.OUT]
    assert pin['state'] in [GPIO.LOW, GPIO.HIGH]
    assert isinstance(pin['configured'], bool)

def test_gpio_configure(client):
    """Test configuring GPIO pins through API."""
    # Configure pin as output
    response = client.post('/gpio/api/configure', json={
        'pin': 18,
        'mode': GPIO.OUT
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == 18
    assert data['mode'] == GPIO.OUT
    assert data['state'] in [GPIO.LOW, GPIO.HIGH]
    
    # Configure pin as input
    response = client.post('/gpio/api/configure', json={
        'pin': 18,
        'mode': GPIO.IN
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == 18
    assert data['mode'] == GPIO.IN
    assert data['state'] in [GPIO.LOW, GPIO.HIGH]

def test_gpio_state_changes(client):
    """Test changing GPIO pin states through API."""
    # Configure pin first
    client.post('/gpio/api/configure', json={
        'pin': 18,
        'mode': GPIO.OUT
    })
    
    # Set HIGH
    response = client.post('/gpio/api/state', json={
        'pin': 18,
        'state': GPIO.HIGH
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == 18
    assert data['state'] == GPIO.HIGH
    
    # Set LOW
    response = client.post('/gpio/api/state', json={
        'pin': 18,
        'state': GPIO.LOW
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['pin'] == 18
    assert data['state'] == GPIO.LOW

def test_gpio_cleanup(client):
    """Test GPIO cleanup through API."""
    response = client.post('/gpio/api/cleanup')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success' 
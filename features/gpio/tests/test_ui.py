"""
UI Tests for GPIO Control Interface
"""
import pytest
from flask import url_for
from flask.testing import FlaskClient

@pytest.fixture
def client(app) -> FlaskClient:
    """Create a test client."""
    return app.test_client()

def test_gpio_page_load(client):
    """Test that the GPIO control page loads correctly."""
    response = client.get('/gpio/')
    assert response.status_code == 200
    assert b"GPIO Control Panel" in response.data
    assert b"gpio-pin-select" in response.data
    assert b"set-input" in response.data
    assert b"set-output" in response.data
    assert b"gpio-overview" in response.data

def test_gpio_api_pins(client):
    """Test the GPIO pins API endpoint."""
    response = client.get('/gpio/api/pins')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert data['status'] == 'success'
    assert 'pins' in data
    assert isinstance(data['pins'], list)
    assert len(data['pins']) > 0

def test_gpio_configure(client):
    """Test configuring a GPIO pin."""
    # Configure pin as output
    response = client.post('/gpio/api/configure', json={
        'pin': 18,
        'mode': 'OUT'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['pin'] == 18
    assert data['mode'] == 'OUT'

def test_gpio_state_changes(client):
    """Test changing GPIO pin states."""
    # Configure pin first
    client.post('/gpio/api/configure', json={
        'pin': 18,
        'mode': 'OUT'
    })
    
    # Set state HIGH
    response = client.post('/gpio/api/state', json={
        'pin': 18,
        'state': 1
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['pin'] == 18
    assert data['state'] == 1
    
    # Set state LOW
    response = client.post('/gpio/api/state', json={
        'pin': 18,
        'state': 0
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['pin'] == 18
    assert data['state'] == 0

def test_gpio_cleanup(client):
    """Test GPIO cleanup endpoint."""
    response = client.post('/gpio/api/cleanup')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'message' in data 
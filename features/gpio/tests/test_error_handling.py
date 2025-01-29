"""
Error Handling Tests for GPIO Functionality
"""
import pytest
from flask import url_for
import json
from unittest.mock import patch, MagicMock
from features.gpio.hardware import GPIO

@pytest.fixture
def mock_gpio_manager():
    """Mock GPIO manager."""
    with patch('features.gpio.routes.gpio_manager') as mock:
        # Set up available pins
        mock.get_available_pins.return_value = [18]
        yield mock

class TestGPIOErrorHandling:
    """Test suite for GPIO error handling."""
    
    def teardown_method(self, method):
        """Clean up after each test."""
        from features.gpio.routes import gpio_manager
        gpio_manager.cleanup()
    
    def test_invalid_pin_number(self, client):
        """Test handling of invalid pin numbers."""
        response = client.post('/gpio/api/configure', json={
            'pin': 999,  # Invalid pin number
            'mode': GPIO.OUT
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid pin number' in data['error']
    
    def test_invalid_pin_mode(self, client):
        """Test handling of invalid pin modes."""
        response = client.post('/gpio/api/configure', json={
            'pin': 18,
            'mode': 'INVALID'  # Invalid mode
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid mode' in data['error']
    
    def test_missing_parameters(self, client):
        """Test handling of missing required parameters."""
        # Test configure endpoint
        response = client.post('/gpio/api/configure', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Missing required parameters' in data['error']
        
        # Test state endpoint
        response = client.post('/gpio/api/state', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Missing required parameters' in data['error']
    
    def test_hardware_access_failure(self, client, mock_gpio_manager):
        """Test handling of hardware access failures."""
        mock_gpio_manager.configure_pin.side_effect = RuntimeError("Hardware access failed")
        
        response = client.post('/gpio/api/configure', json={
            'pin': 18,
            'mode': GPIO.OUT
        })
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Hardware access failed' in data['error']
    
    def test_concurrent_access(self, client):
        """Test handling of concurrent access to GPIO."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            """Make a GPIO request."""
            try:
                response = client.post('/gpio/api/configure', json={
                    'pin': 18,
                    'mode': GPIO.OUT
                })
                results.put(response.status_code)
            except Exception as e:
                results.put(e)
        
        # Create multiple threads to simulate concurrent access
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Check that all requests completed successfully
        while not results.empty():
            result = results.get()
            assert result == 200
    
    def test_cleanup_error_handling(self, client, mock_gpio_manager):
        """Test handling of cleanup failures."""
        mock_gpio_manager.cleanup.side_effect = RuntimeError("Cleanup failed")
        
        response = client.post('/gpio/api/cleanup')
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Cleanup failed' in data['error']
    
    def test_invalid_state_value(self, client):
        """Test handling of invalid state values."""
        # Configure pin first
        client.post('/gpio/api/configure', json={
            'pin': 18,
            'mode': GPIO.OUT
        })
        
        # Try to set invalid state
        response = client.post('/gpio/api/state', json={
            'pin': 18,
            'state': 2  # Invalid state value
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid state value' in data['error']
    
    def test_unconfigured_pin_access(self, client):
        """Test handling of access to unconfigured pins."""
        response = client.post('/gpio/api/state', json={
            'pin': 18,
            'state': GPIO.HIGH
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not configured' in data['error']
    
    def test_input_pin_write(self, client):
        """Test handling of attempts to write to input pins."""
        # Configure pin as input
        client.post('/gpio/api/configure', json={
            'pin': 18,
            'mode': GPIO.IN
        })
        
        # Try to set state
        response = client.post('/gpio/api/state', json={
            'pin': 18,
            'state': GPIO.HIGH
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not configured as output' in data['error']
    
    def test_malformed_json(self, client):
        """Test handling of malformed JSON requests."""
        response = client.post('/gpio/api/configure', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data 
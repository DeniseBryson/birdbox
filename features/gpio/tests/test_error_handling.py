"""
Error Handling Tests for GPIO Functionality
"""
import pytest
from flask import url_for
import json
from unittest.mock import patch, MagicMock
from features.gpio.hardware import GPIO

@pytest.fixture
def mock_gpio():
    """Mock GPIO hardware interface."""
    with patch('features.gpio.hardware.GPIO') as mock:
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
            'mode': 'OUT'
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid GPIO pin' in data['message']
    
    def test_invalid_pin_mode(self, client):
        """Test handling of invalid pin modes."""
        response = client.post('/gpio/api/configure', json={
            'pin': 18,
            'mode': 'INVALID'  # Invalid mode
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid mode' in data['message']
    
    def test_missing_parameters(self, client):
        """Test handling of missing required parameters."""
        # Test configure endpoint
        response = client.post('/gpio/api/configure', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Missing required fields' in data['message']
        
        # Test state endpoint
        response = client.post('/gpio/api/state', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Missing required fields' in data['message']
    
    def test_hardware_access_failure(self, client):
        """Test handling of hardware access failures."""
        with patch('features.gpio.routes.gpio_manager') as mock_manager:
            mock_manager.configure_pin.side_effect = RuntimeError("Hardware access failed")
            
            response = client.post('/gpio/api/configure', json={
                'pin': 18,
                'mode': 'OUT'
            })
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'Hardware access failed' in data['message']
    
    def test_concurrent_access(self, client):
        """Test handling of concurrent pin access."""
        # Configure pin first
        client.post('/gpio/api/configure', json={
            'pin': 18,
            'mode': 'OUT'
        })
        
        # Attempt concurrent state changes
        import threading
        import queue
        
        results = queue.Queue()
        def make_request():
            response = client.post('/gpio/api/state', json={
                'pin': 18,
                'state': 1
            })
            results.put(response)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Check all responses
        while not results.empty():
            response = results.get()
            assert response.status_code in [200, 409]  # Either success or conflict
    
    def test_cleanup_error_handling(self, client):
        """Test handling of cleanup errors."""
        with patch('features.gpio.routes.gpio_manager') as mock_manager:
            mock_manager.cleanup.side_effect = RuntimeError("Cleanup failed")
            
            response = client.post('/gpio/api/cleanup')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'Cleanup failed' in data['message']
    
    def test_invalid_state_value(self, client):
        """Test handling of invalid state values."""
        response = client.post('/gpio/api/state', json={
            'pin': 18,
            'state': 'invalid'  # Should be 0 or 1
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid state value' in data['message']
    
    def test_unconfigured_pin_access(self, client):
        """Test handling of accessing unconfigured pins."""
        # Try to set state without configuring first
        response = client.post('/gpio/api/state', json={
            'pin': 18,
            'state': 1
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Pin not configured' in data['message']
    
    def test_input_pin_write(self, client):
        """Test handling of writing to input pins."""
        # Configure pin as input
        client.post('/gpio/api/configure', json={
            'pin': 18,
            'mode': 'IN'
        })
        
        # Try to set state
        response = client.post('/gpio/api/state', json={
            'pin': 18,
            'state': 1
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Cannot set state of input pin' in data['message']
    
    def test_malformed_json(self, client):
        """Test handling of malformed JSON requests."""
        response = client.post('/gpio/api/configure',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
        assert '400 BAD REQUEST' in response.status 
"""Integration tests for camera streaming."""

import pytest
from app import create_app

def test_stream_endpoint_exists():
    """Test that camera stream endpoint exists."""
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Test endpoint exists
    response = client.get('/api/v1/camera/stream')
    
    # Verify response
    assert response.status_code != 404  # Endpoint exists
    assert response.status_code in [200, 101, 426]  # OK, Switching Protocols, or Upgrade Required 
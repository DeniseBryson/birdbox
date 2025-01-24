"""
Tests for camera routes
"""
import pytest
from unittest.mock import patch
from flask import Flask
from features.camera.routes import camera_bp, get_camera_manager

@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    app.register_blueprint(camera_bp)
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_get_camera_status(client):
    """Test camera status endpoint"""
    with patch('features.camera.camera.Camera') as mock_camera_cls:
        mock_camera_cls.list_cameras.return_value = [
            {'id': 0, 'status': 'available'}
        ]
        
        response = client.get('/api/v1/camera/status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert 'available_cameras' in data

def test_initialize_camera(client, app):
    """Test camera initialization endpoint"""
    with app.test_request_context():
        with patch.object(get_camera_manager(), 'initialize_camera', return_value=True):
            response = client.post('/api/v1/camera/initialize/0')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'message' in data

def test_initialize_camera_failure(client, app):
    """Test camera initialization failure"""
    with app.test_request_context():
        with patch.object(get_camera_manager(), 'initialize_camera', return_value=False):
            response = client.post('/api/v1/camera/initialize/0')
            assert response.status_code == 500
            
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'message' in data

def test_stop_camera(client, app):
    """Test camera stop endpoint"""
    with app.test_request_context():
        with patch.object(get_camera_manager(), 'stop_camera'):
            response = client.post('/api/v1/camera/stop')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'message' in data 
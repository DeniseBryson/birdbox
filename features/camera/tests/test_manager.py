"""
Tests for camera manager functionality
"""
import pytest
from unittest.mock import Mock, patch
import numpy as np
from features.camera.manager import CameraManager
from features.camera.camera import Camera

@pytest.fixture
def mock_camera_manager():
    """Create a camera manager instance with mocked camera"""
    with patch('features.camera.camera.Camera') as mock_camera_cls:
        # Setup mock camera
        mock_camera = Mock()
        mock_camera.start.return_value = True
        mock_camera.is_running = True
        mock_camera.get_frame.return_value = (True, b'test_frame')
        mock_camera.get_camera_info.return_value = {
            'id': 0,
            'resolution': (1280, 720),
            'is_running': True,
            'status': 'active'
        }
        
        mock_camera_cls.return_value = mock_camera
        mock_camera_cls.list_cameras.return_value = [
            {'id': 0, 'status': 'available'}
        ]
        
        manager = CameraManager()
        yield manager

def test_manager_initialization():
    """Test manager initialization"""
    manager = CameraManager()
    assert manager._camera is None
    assert manager._active_camera_id is None

def test_initialize_camera(mock_camera_manager):
    """Test camera initialization through manager"""
    assert mock_camera_manager.initialize_camera(camera_id=0) == True
    assert mock_camera_manager._active_camera_id == 0
    assert mock_camera_manager._camera is not None

def test_stop_camera(mock_camera_manager):
    """Test camera stop through manager"""
    mock_camera_manager.initialize_camera(camera_id=0)
    mock_camera_manager.stop_camera()
    assert mock_camera_manager._camera is None
    assert mock_camera_manager._active_camera_id is None

def test_get_camera_status_no_camera():
    """Test status retrieval with no active camera"""
    with patch('features.camera.camera.Camera') as mock_camera_cls:
        mock_camera_cls.list_cameras.return_value = [
            {'id': 0, 'status': 'available'}
        ]
        
        manager = CameraManager()
        status = manager.get_camera_status()
        
        assert status['active_camera'] is None
        assert status['status'] == 'inactive'
        assert len(status['available_cameras']) > 0

def test_get_camera_status_with_camera(mock_camera_manager):
    """Test status retrieval with active camera"""
    mock_camera_manager.initialize_camera(camera_id=0)
    status = mock_camera_manager.get_camera_status()
    
    assert status['active_camera'] == 0
    assert status['status'] == 'active'
    assert 'camera_info' in status
    assert len(status['available_cameras']) > 0

def test_get_frame(mock_camera_manager):
    """Test frame retrieval through manager"""
    mock_camera_manager.initialize_camera(camera_id=0)
    success, frame = mock_camera_manager.get_frame()
    
    assert success == True
    assert isinstance(frame, bytes)  # Just check it's bytes, actual content will vary

def test_get_frame_no_camera():
    """Test frame retrieval with no camera"""
    manager = CameraManager()
    success, frame = manager.get_frame()
    
    assert success == False
    assert frame is None

def test_manager_cleanup(mock_camera_manager):
    """Test manager cleanup on deletion"""
    mock_camera_manager.initialize_camera(camera_id=0)
    assert mock_camera_manager._camera is not None
    
    mock_camera_manager.__del__()
    assert mock_camera_manager._camera is None 
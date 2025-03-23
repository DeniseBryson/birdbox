"""
Tests for camera functionality
"""
import pytest
from unittest.mock import Mock, patch
import cv2
import numpy as np
from features.camera.camera import Camera

@pytest.fixture
def mock_camera():
    """Create a camera instance with mocked cv2"""
    with patch('cv2.VideoCapture') as mock_cap:
        # Setup mock camera
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))
        mock_cap.return_value.set.return_value = True
        
        camera = Camera(camera_id=0)
        yield camera

def test_camera_initialization(mock_camera):
    """Test camera initialization"""
    assert mock_camera.camera_id == 0
    assert mock_camera.is_running == False
    assert mock_camera.cap is None

def test_camera_start(mock_camera):
    """Test camera start functionality"""
    assert mock_camera.start() == True
    assert mock_camera.is_running == True
    assert mock_camera.cap is not None

def test_camera_stop(mock_camera):
    """Test camera stop functionality"""
    mock_camera.start()
    mock_camera.stop()
    assert mock_camera.is_running == False
    assert mock_camera.cap is not None  # cap exists but is released

def test_get_frame(mock_camera):
    """Test frame capture"""
    mock_camera.start()
    success, frame = mock_camera.get_frame()
    assert success == True
    assert isinstance(frame, bytes)

def test_get_camera_info(mock_camera):
    """Test camera info retrieval"""
    info = mock_camera.get_camera_info()
    assert isinstance(info, dict)
    assert 'id' in info
    assert 'resolution' in info
    assert isinstance(info['resolution'], tuple)
    assert len(info['resolution']) == 2
    assert 'is_running' in info
    assert isinstance(info['is_running'], bool)
    assert 'status' in info
    assert info['status'] in ['active', 'stopped']
    assert 'is_recording' in info
    assert isinstance(info['is_recording'], bool)

@patch('cv2.VideoCapture')
def test_list_cameras(mock_cap):
    """Test camera listing functionality"""
    # Setup mock camera behavior
    mock_cap.return_value.isOpened.return_value = True
    mock_cap.return_value.read.return_value = (True, None)
    
    # Test camera listing with max_cameras=2
    cameras = Camera.list_cameras(max_cameras=2)
    
    # Verify results
    assert isinstance(cameras, list)
    assert len(cameras) <= 2  # Should not exceed max_cameras
    assert len(cameras) >= 0  # Should have zero or more cameras
    
    # Verify camera properties
    for camera in cameras:
        assert isinstance(camera['id'], int)  # Should have numeric ID
        assert camera['id'] >= 0  # ID should be non-negative
        assert 'name' in camera  # Should have a name
        assert camera['name'] == f'Camera {camera["id"]}'  # Name should match ID
    
    # Verify VideoCapture was called
    assert mock_cap.call_count > 0  # Should try at least once
    mock_cap.assert_any_call(0)  # Should always try camera 0

def test_camera_cleanup(mock_camera):
    """Test camera cleanup on deletion"""
    mock_camera.start()
    assert mock_camera.is_running == True
    mock_camera.__del__()
    assert mock_camera.is_running == False 
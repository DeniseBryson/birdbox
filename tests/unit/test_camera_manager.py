"""Unit tests for camera manager."""

import unittest
from unittest.mock import Mock, patch
import cv2
import numpy as np
from features.camera.camera_manager import CameraManager

class TestCameraManager(unittest.TestCase):
    """Test cases for CameraManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.camera_manager = CameraManager()
        # Create a mock frame for testing
        self.mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        ret, self.mock_jpeg = cv2.imencode('.jpg', self.mock_frame)
        # Replace the lock with a dummy that doesn't block
        self.camera_manager.lock = type('DummyLock', (), {
            '__enter__': lambda *args: None,
            '__exit__': lambda *args: None,
        })()
    
    def tearDown(self):
        """Clean up after tests."""
        self.camera_manager.stop()
    
    def create_mock_camera(self, mock_capture):
        """Create a properly configured mock camera."""
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480
        }.get(prop, 0)  # Default to 0 for other properties
        mock_camera.set.return_value = True
        mock_camera.read.return_value = (True, self.mock_frame)
        mock_capture.return_value = mock_camera
        return mock_camera
    
    @patch('cv2.VideoCapture')
    def test_initialize_success(self, mock_capture):
        """Test successful camera initialization."""
        # Setup mock
        mock_camera = self.create_mock_camera(mock_capture)
        
        # Test
        result = self.camera_manager.initialize()
        
        # Assert
        self.assertTrue(result)
        self.assertTrue(self.camera_manager.is_initialized)
        mock_camera.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 640)
        mock_camera.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    @patch('cv2.VideoCapture')
    def test_initialize_failure(self, mock_capture):
        """Test camera initialization failure."""
        # Setup mock
        mock_camera = Mock(spec=['isOpened', 'release'])
        mock_camera.isOpened.return_value = False
        mock_camera.release.return_value = None
        mock_capture.return_value = mock_camera
        
        # Set up initial camera state
        self.camera_manager.camera = mock_camera
        self.camera_manager.is_initialized = True
        
        # Test and assert
        with self.assertRaises(RuntimeError):
            self.camera_manager.initialize()
        self.assertFalse(self.camera_manager.is_initialized)
        mock_camera.isOpened.assert_called_once()
        mock_camera.release.assert_called_once()
    
    @patch('cv2.VideoCapture')
    def test_get_frame_success(self, mock_capture):
        """Test successful frame capture."""
        # Setup mock
        mock_camera = self.create_mock_camera(mock_capture)
        
        # Initialize camera
        self.camera_manager.initialize()
        
        # Test
        frame = self.camera_manager.get_frame()
        
        # Assert
        self.assertIsNotNone(frame)
        mock_camera.read.assert_called_once()
    
    @patch('cv2.VideoCapture')
    def test_get_frame_failure(self, mock_capture):
        """Test frame capture failure."""
        # Setup mock
        mock_camera = self.create_mock_camera(mock_capture)
        mock_camera.read.return_value = (False, None)
        
        # Initialize camera
        self.camera_manager.initialize()
        
        # Test
        frame = self.camera_manager.get_frame()
        
        # Assert
        self.assertIsNone(frame)
    
    def test_get_frame_not_initialized(self):
        """Test get_frame when camera is not initialized."""
        with self.assertRaises(RuntimeError):
            self.camera_manager.get_frame()
    
    @patch('cv2.VideoCapture')
    def test_get_resolution(self, mock_capture):
        """Test getting camera resolution."""
        # Setup mock
        mock_camera = self.create_mock_camera(mock_capture)
        
        # Initialize camera
        self.camera_manager.initialize()
        
        # Test
        resolution = self.camera_manager.get_resolution()
        
        # Assert
        self.assertEqual(resolution['width'], 640)
        self.assertEqual(resolution['height'], 480)
    
    @patch('cv2.VideoCapture')
    def test_stop(self, mock_capture):
        """Test camera stop/cleanup."""
        # Setup mock
        mock_camera = self.create_mock_camera(mock_capture)
        
        # Initialize and stop camera
        self.camera_manager.initialize()
        self.camera_manager.stop()
        
        # Assert
        mock_camera.release.assert_called_once()
        self.assertFalse(self.camera_manager.is_initialized)
        self.assertIsNone(self.camera_manager.camera)

if __name__ == '__main__':
    unittest.main() 
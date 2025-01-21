"""
Tests for the Camera implementation
"""
import unittest
import cv2
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hardware.camera import Camera
from src.utils.storage_manager import StorageManager
from src.routes.camera_routes import camera_bp
from datetime import datetime
import time
import os
from pathlib import Path
import json
from flask import Flask

class TestCamera(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock frame for testing
        self.test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(
            self.test_frame,
            'Test Frame',
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
    @patch('cv2.VideoCapture')
    def test_camera_initialization(self, mock_capture):
        """Test camera initialization with default parameters"""
        # Setup mock
        mock_capture.return_value.isOpened.return_value = True
        
        # Create camera instance
        camera = Camera()
        
        # Assert initial state
        self.assertEqual(camera.camera_id, 0)
        self.assertEqual(camera.resolution, (1280, 720))
        self.assertFalse(camera.is_running)
        self.assertFalse(camera.is_recording)
        self.assertEqual(len(camera.recording_frames), 0)
        self.assertIsNone(camera.start_time)
        
    @patch('cv2.VideoCapture')
    def test_list_cameras(self, mock_capture):
        """Test camera detection"""
        # Setup mock to simulate two cameras
        def mock_open(index):
            mock = Mock()
            if index < 2:
                mock.isOpened.return_value = True
                mock.get.side_effect = lambda x: 1280 if x == cv2.CAP_PROP_FRAME_WIDTH else 720
            else:
                mock.isOpened.return_value = False
            return mock
            
        mock_capture.side_effect = mock_open
        
        # Get camera list
        cameras = Camera.list_cameras()
        
        # Assert results
        self.assertEqual(len(cameras), 2)
        self.assertEqual(cameras[0]['id'], 0)
        self.assertEqual(cameras[0]['resolution'], (1280, 720))
        self.assertEqual(cameras[0]['status'], 'available')
        
    @patch('cv2.VideoCapture')
    def test_camera_start_stop(self, mock_capture):
        """Test starting and stopping the camera"""
        # Setup mock
        mock_capture.return_value.isOpened.return_value = True
        
        # Create and start camera
        camera = Camera()
        camera.start()
        
        # Assert camera is running
        self.assertTrue(camera.is_running)
        self.assertIsNotNone(camera.start_time)
        self.assertIsNotNone(camera.thread)
        
        # Stop camera
        camera.stop()
        
        # Assert camera is stopped
        self.assertFalse(camera.is_running)
        
    @patch('cv2.VideoCapture')
    def test_motion_detection(self, mock_capture):
        """Test motion detection functionality"""
        # Setup mock
        mock_capture.return_value.isOpened.return_value = True
        mock_capture.return_value.read.return_value = (True, self.test_frame)
        
        # Create camera instance
        camera = Camera()
        camera.start()
        
        # Let the camera thread run for a moment
        time.sleep(0.1)
        
        # Get frame and check motion detection
        frame = camera.get_frame()
        self.assertIsNotNone(frame)
        self.assertIsInstance(camera.motion_detected, bool)
        
        camera.stop()
        
    @patch('cv2.VideoCapture')
    def test_recording(self, mock_capture):
        """Test recording functionality"""
        # Setup mock
        mock_capture.return_value.isOpened.return_value = True
        mock_capture.return_value.read.return_value = (True, self.test_frame)
        
        # Create camera instance
        camera = Camera()
        camera.start()
        
        # Start recording
        camera.start_recording()
        self.assertTrue(camera.is_recording)
        
        # Let it record a few frames
        time.sleep(0.1)
        
        # Stop recording
        frames = camera.stop_recording()
        
        # Assert recording results
        self.assertFalse(camera.is_recording)
        self.assertGreater(len(frames), 0)
        self.assertEqual(frames[0].shape, self.test_frame.shape)
        
        camera.stop()
        
    @patch('cv2.VideoCapture')
    def test_resolution_change(self, mock_capture):
        """Test changing camera resolution"""
        # Setup mock
        mock_capture.return_value.isOpened.return_value = True
        
        # Create camera instance
        camera = Camera()
        camera.start()
        
        # Change resolution
        new_resolution = (1920, 1080)
        camera.resolution = new_resolution
        
        # Assert resolution change
        self.assertEqual(camera.resolution, new_resolution)
        
        camera.stop()
        
    @patch('cv2.VideoCapture')
    def test_camera_info(self, mock_capture):
        """Test camera information retrieval"""
        # Setup mock
        mock_capture.return_value.isOpened.return_value = True
        mock_capture.return_value.read.return_value = (True, self.test_frame)
        
        # Create camera instance
        camera = Camera(camera_id=1, resolution=(1920, 1080))
        camera.start()
        
        # Let it run for a moment to get some frames
        time.sleep(0.1)
        
        # Get camera info
        info = camera.get_camera_info()
        
        # Assert info contents
        self.assertEqual(info['id'], 1)
        self.assertEqual(info['resolution'], (1920, 1080))
        self.assertIn('fps', info)
        self.assertGreaterEqual(info['fps'], 0)  # FPS should be non-negative
        self.assertIn('is_recording', info)
        self.assertIn('motion_detected', info)
        self.assertIn('frame_count', info)
        self.assertGreater(info['frame_count'], 0)  # Should have captured some frames
        self.assertEqual(info['status'], 'active')
        
        camera.stop()
        self.assertEqual(camera.get_camera_info()['status'], 'stopped')
        
    @patch('cv2.VideoCapture')
    def test_error_handling(self, mock_capture):
        """Test error handling in camera operations"""
        # Test camera open failure
        mock_capture.return_value.isOpened.return_value = False
        camera = Camera()
        
        with self.assertRaises(RuntimeError):
            camera.start()
            
        # Test frame read failure
        mock_capture.return_value.isOpened.return_value = True
        mock_capture.return_value.read.return_value = (False, None)
        
        camera = Camera()
        camera.start()
        time.sleep(0.1)
        
        frame = camera.get_frame()
        self.assertIsNone(frame)
        
        camera.stop()

class TestCameraAPI(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create Flask test app
        self.app = Flask(__name__)
        self.app.config.from_object('config.default')
        
        # Setup storage
        self.base_path = Path(__file__).parent.parent / 'data' / 'recordings'
        os.makedirs(self.base_path, exist_ok=True)
        
        # Initialize storage manager
        from app import storage_manager, app as main_app
        storage_manager.base_path = self.base_path
        storage_manager.cleanup_failed_recordings()
        
        # Copy routes and rules from main app
        for endpoint, view_func in main_app.view_functions.items():
            if not endpoint.startswith('camera.'):  # Skip camera routes as they're in blueprint
                self.app.view_functions[endpoint] = view_func
                
        # Copy URL rules
        for rule in main_app.url_map.iter_rules():
            if not rule.endpoint.startswith('camera.'):  # Skip camera routes
                self.app.url_map.add(rule.empty())
        
        # Register blueprint after main routes
        self.app.register_blueprint(camera_bp)
        
        # Create test client
        self.client = self.app.test_client()
        
        # Reset camera
        import src.routes.camera_routes as camera_routes
        camera_routes.camera = None
        
    def tearDown(self):
        """Clean up after each test"""
        import src.routes.camera_routes as camera_routes
        if camera_routes.camera:
            camera_routes.camera.stop()
            camera_routes.camera = None
        
    def test_list_cameras_endpoint(self):
        """Test /api/cameras endpoint"""
        response = self.client.get('/api/cameras')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            camera = data[0]
            self.assertIn('id', camera)
            self.assertIn('name', camera)
            self.assertIn('resolution', camera)
            self.assertIn('status', camera)
        
    def test_camera_selection(self):
        """Test camera selection endpoint"""
        response = self.client.post('/api/camera/select', json={'camera_id': 0})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('camera', data)

    def test_camera_status(self):
        """Test camera status endpoint"""
        # First select a camera
        self.client.post('/api/camera/select', json={'camera_id': 0})
        
        # Wait for camera to initialize
        time.sleep(0.5)
        
        # Then get status
        response = self.client.get('/api/camera/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('fps', data)
        self.assertIn('resolution', data)
        self.assertIn('is_recording', data)
        self.assertIn('status', data)

    def test_camera_settings(self):
        """Test camera settings endpoint"""
        # First select a camera
        self.client.post('/api/camera/select', json={'camera_id': 0})
        
        # Update settings
        response = self.client.post('/api/camera/settings', 
                               json={'resolution': [1920, 1080]})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        
        # Verify settings were updated
        response = self.client.get('/api/camera/status')
        data = response.get_json()
        self.assertEqual(data['resolution'], [1920, 1080])

    def test_recording_cycle(self):
        """Test complete recording cycle"""
        # Select camera
        self.client.post('/api/camera/select', json={'camera_id': 0})
        
        # Start recording
        response = self.client.post('/api/camera/record/start')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        
        # Wait for frames to be captured
        time.sleep(0.5)  # Increased wait time to ensure frames are captured
        
        # Stop recording
        response = self.client.post('/api/camera/record/stop')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('path', data)
        self.assertIn('frame_count', data)
        self.assertGreater(data['frame_count'], 0)
        path = data['path']
        self.assertTrue(isinstance(path, str))  # Path should be serialized as string
        self.assertTrue(os.path.exists(path))  # File should exist
        
        # Clean up
        if os.path.exists(path):
            os.remove(path)

    def test_error_handling(self):
        """Test error handling in API endpoints"""
        # Test camera status without selection
        response = self.client.get('/api/camera/status')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No camera selected')
        
        # Test invalid camera selection
        response = self.client.post('/api/camera/select', json={'camera_id': 999})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['status'], 'error')

    def test_storage_management(self):
        """Test storage management during recording"""
        # Select camera
        self.client.post('/api/camera/select', json={'camera_id': 0})
        
        # Get initial storage status
        response = self.client.get('/api/storage/status')
        self.assertEqual(response.status_code, 200)
        initial_status = response.get_json()
        self.assertIn('total_bytes', initial_status)
        self.assertIn('used_bytes', initial_status)
        self.assertIn('available_bytes', initial_status)
        
        # Record a short video
        self.client.post('/api/camera/record/start')
        time.sleep(0.5)  # Increased wait time to ensure frames are captured
        response = self.client.post('/api/camera/record/stop')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('path', data)
        self.assertGreater(data['frame_count'], 0)
        
        # Get updated storage status
        response = self.client.get('/api/storage/status')
        self.assertEqual(response.status_code, 200)
        updated_status = response.get_json()
        
        # Verify storage was updated
        self.assertGreater(updated_status['used_bytes'], initial_status['used_bytes'])

    def test_camera_stop(self):
        """Test camera stop endpoint"""
        # First select and start a camera
        response = self.client.post('/api/camera/select', json={'camera_id': 0})
        self.assertEqual(response.status_code, 200)
        
        # Verify camera is running
        response = self.client.get('/api/camera/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'active')
        
        # Stop the camera
        response = self.client.post('/api/camera/stop')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Camera stopped')
        
        # Verify camera is stopped
        response = self.client.get('/api/camera/status')
        self.assertEqual(response.status_code, 400)  # Should fail as no camera is selected
        data = response.get_json()
        self.assertEqual(data['error'], 'No camera selected')

if __name__ == '__main__':
    unittest.main() 
"""
Integration tests for camera and storage functionality
"""
import unittest
import os
import shutil
from pathlib import Path
from flask import Flask, url_for, render_template
from src.routes.camera_routes import camera_bp
from src.core.utils.storage import StorageManager
from src.routes.storage_routes import storage_bp
from src.routes.gpio_routes import gpio_bp
import tempfile
import json
from unittest.mock import Mock, patch
import numpy as np
import cv2

class TestCameraIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create Flask test app
        self.app = Flask(__name__)
        self.app.template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.app.static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        
        # Create test directories
        self.test_dir = tempfile.mkdtemp()
        self.recordings_dir = Path(self.test_dir) / 'recordings'
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage manager
        self.storage_manager = StorageManager(self.test_dir, storage_limit_gb=1.0)
        
        # Mock camera
        self.mock_camera = Mock()
        self.mock_camera.is_running = True
        self.mock_camera.is_recording = False
        self.mock_camera.resolution = (1280, 720)
        self.mock_camera.frame_count = 0
        self.mock_camera.start_time = None
        self.mock_camera.motion_detected = False
        self.mock_camera.camera_id = 0
        
        # Mock camera methods
        self.mock_camera.start.return_value = None
        self.mock_camera.stop.return_value = None
        self.mock_camera.start_recording.return_value = None
        self.mock_camera.stop_recording.return_value = [np.zeros((720, 1280, 3), dtype=np.uint8)]
        self.mock_camera.get_camera_info.return_value = {
            'id': 0,
            'name': 'Test Camera',
            'resolution': (1280, 720),
            'status': 'active'
        }
        self.mock_camera.list_cameras.return_value = [{
            'id': 0,
            'name': 'Test Camera',
            'resolution': (1280, 720),
            'status': 'available'
        }]
        
        # Mock capture
        self.mock_capture = Mock()
        self.mock_capture.isOpened.return_value = True
        self.mock_capture.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))
        self.mock_capture.get.side_effect = lambda x: {
            cv2.CAP_PROP_FRAME_WIDTH: 1280,
            cv2.CAP_PROP_FRAME_HEIGHT: 720,
            cv2.CAP_PROP_FPS: 30.0
        }.get(x, 0)
        
        self.mock_camera.cap = self.mock_capture
        
        # Add routes
        @self.app.route('/')
        def index():
            return render_template('index.html')
            
        # Register blueprints
        self.app.register_blueprint(camera_bp)
        self.app.register_blueprint(storage_bp)
        self.app.register_blueprint(gpio_bp)
        
        # Create test client
        self.client = self.app.test_client()
        
        # Start patching
        self.camera_patcher = patch('src.hardware.camera.Camera')
        self.mock_camera_class = self.camera_patcher.start()
        self.mock_camera_class.return_value = self.mock_camera
        
    def tearDown(self):
        """Clean up test environment"""
        self.camera_patcher.stop()
        shutil.rmtree(self.test_dir)
        
    def test_directory_structure(self):
        """Test that recordings are stored in the correct directory"""
        # Verify recordings directory exists
        self.assertTrue(self.recordings_dir.exists())
        self.assertTrue(self.recordings_dir.is_dir())
        
        # Create a test recording with content
        test_recording = self.recordings_dir / "20250101_000000.avi"
        with open(test_recording, 'wb') as f:
            # Write a minimal but valid AVI header
            f.write(b'RIFF')  # RIFF header
            f.write(b'\x00\x00\x00\x00')  # File size (placeholder)
            f.write(b'AVI ')  # RIFF type
            f.write(b'LIST')  # LIST chunk
            f.write(b'\x00\x00\x00\x00')  # List size (placeholder)
            f.write(b'hdrl')  # List type
            f.write(b'\x00' * 1024)  # Padding to make it look like a real file
        
        # Verify storage manager finds the recording
        recordings = self.storage_manager.get_recordings_list()
        self.assertEqual(len(recordings), 1)
        
    def test_camera_auto_start(self):
        """Test that camera page automatically starts a camera"""
        with self.app.test_request_context():
            # Mock camera list
            self.mock_camera.list_cameras.return_value = [{
                'id': 0,
                'name': 'Test Camera',
                'resolution': (1280, 720),
                'status': 'available'
            }]
            
            # Access camera page
            response = self.client.get('/camera')
            self.assertEqual(response.status_code, 200)
            
            # Check if camera status indicates it's running
            status_response = self.client.get('/api/camera/status')
            self.assertEqual(status_response.status_code, 200)
            
            status_data = json.loads(status_response.data)
            self.assertTrue(status_data.get('is_running', False))
            
    def test_recordings_endpoint(self):
        """Test the recordings list endpoint"""
        # Create some test recordings with content
        test_files = [
            "20250101_000000.avi",
            "20250101_000001.avi",
            "20250101_000002.avi"
        ]
        
        for filename in test_files:
            with open(self.recordings_dir / filename, 'wb') as f:
                # Write a minimal but valid AVI header
                f.write(b'RIFF')  # RIFF header
                f.write(b'\x00\x00\x00\x00')  # File size (placeholder)
                f.write(b'AVI ')  # RIFF type
                f.write(b'LIST')  # LIST chunk
                f.write(b'\x00\x00\x00\x00')  # List size (placeholder)
                f.write(b'hdrl')  # List type
                f.write(b'\x00' * 1024)  # Padding to make it look like a real file
        
        # Test recordings endpoint
        response = self.client.get('/api/camera/recordings')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['recordings']), 3)
        
        # Verify recording metadata
        for recording in data['recordings']:
            self.assertIn('id', recording)
            self.assertIn('filename', recording)
            self.assertIn('timestamp', recording)
            self.assertIn('size', recording)
            
    def test_camera_status_endpoint(self):
        """Test the camera status endpoint"""
        response = self.client.get('/api/camera/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('is_running', data)
        self.assertIn('fps', data)
        self.assertIn('motion_detected', data)
        self.assertIn('frame_count', data)
        
    def test_storage_status_endpoint(self):
        """Test the storage status endpoint"""
        response = self.client.get('/api/storage/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('total_bytes', data)
        self.assertIn('used_bytes', data)
        self.assertIn('available_bytes', data)
        self.assertIn('usage_percent', data)
        
    def test_storage_manager_file_handling(self):
        """Test that storage manager correctly handles different file types"""
        # Create various file types
        test_files = {
            'valid': [
                "20250101_000000.avi",  # Valid format
                "20250101_000001.avi"   # Valid format
            ],
            'invalid': [
                "test.txt",             # Wrong extension
                "invalid.mp4",          # Wrong extension
                ".hidden.avi",          # Hidden file
                "bad_format.avi"        # Wrong name format
            ]
        }
        
        # Create test files with content
        for filename in test_files['valid']:
            with open(self.recordings_dir / filename, 'wb') as f:
                # Write a minimal but valid AVI header
                f.write(b'RIFF')  # RIFF header
                f.write(b'\x00\x00\x00\x00')  # File size (placeholder)
                f.write(b'AVI ')  # RIFF type
                f.write(b'LIST')  # LIST chunk
                f.write(b'\x00\x00\x00\x00')  # List size (placeholder)
                f.write(b'hdrl')  # List type
                f.write(b'\x00' * 1024)  # Padding to make it look like a real file
        
        for filename in test_files['invalid']:
            (self.recordings_dir / filename).touch()
        
        # Get recordings list
        recordings = self.storage_manager.get_recordings_list()
        
        # Verify only valid files are listed
        self.assertEqual(len(recordings), len(test_files['valid']))
            
    def test_relative_urls(self):
        """Test that API endpoints use relative URLs"""
        with self.app.test_request_context():
            # Mock camera list for camera page
            self.mock_camera.list_cameras.return_value = [{
                'id': 0,
                'name': 'Test Camera',
                'resolution': (1280, 720),
                'status': 'available'
            }]
            
            # Get camera page
            response = self.client.get('/camera')
            self.assertEqual(response.status_code, 200)
            
            # Check that the page doesn't contain hardcoded URLs
            self.assertNotIn(b'http://localhost', response.data)
            self.assertNotIn(b'https://localhost', response.data)
            
            # Check API endpoints
            endpoints = [
                '/api/camera/status',
                '/api/camera/recordings',
                '/api/storage/status'
            ]
            
            for endpoint in endpoints:
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)
                
                # Verify response doesn't contain absolute URLs
                data = json.loads(response.data)
                self._check_no_absolute_urls(data)
                
    def _check_no_absolute_urls(self, data):
        """Helper method to recursively check for absolute URLs in response data"""
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, str):
                    self.assertNotIn('http://', value.lower())
                    self.assertNotIn('https://', value.lower())
                else:
                    self._check_no_absolute_urls(value)
        elif isinstance(data, list):
            for item in data:
                self._check_no_absolute_urls(item)
                
if __name__ == '__main__':
    unittest.main() 
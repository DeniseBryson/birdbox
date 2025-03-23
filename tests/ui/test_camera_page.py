"""UI tests for camera page using Flask test client."""

import unittest
import json
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup
from app import create_app

class TestCameraPage(unittest.TestCase):
    """Test cases for camera page UI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create patcher for CameraManager
        self.camera_patcher = patch('features.camera.routes.CameraManager')
        self.mock_camera_class = self.camera_patcher.start()
        
        # Setup mock camera
        self.mock_camera = Mock()
        self.mock_camera.initialize.return_value = True
        self.mock_camera.start_recording.return_value = True
        self.mock_camera.stop_recording.return_value = True
        self.mock_camera.get_resolution.return_value = {'width': 640, 'height': 480}
        self.mock_camera_class.return_value = self.mock_camera
        
    def tearDown(self):
        """Clean up after each test."""
        self.camera_patcher.stop()
        
    def test_page_elements(self):
        """Test presence of required page elements."""
        response = self.client.get('/camera/')
        self.assertEqual(response.status_code, 200)
        
        # Parse HTML
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Check title
        title = soup.find('h1')
        self.assertIsNotNone(title)
        self.assertEqual(title.text, 'Camera Control')
        
        # Check stream container
        stream_container = soup.find(id='camera-feed')
        self.assertIsNotNone(stream_container)
        
        # Check stream elements
        stream_image = soup.find(id='stream-image')
        self.assertIsNotNone(stream_image)
        self.assertEqual(stream_image.get('style'), 'display: none;')
        
        placeholder = soup.find(id='stream-placeholder')
        self.assertIsNotNone(placeholder)
        self.assertEqual(placeholder.text, 'Connecting to camera...')
        
        # Check control buttons
        start_button = soup.find(id='start-stream')
        stop_button = soup.find(id='stop-stream')
        self.assertIsNotNone(start_button)
        self.assertIsNotNone(stop_button)
        self.assertEqual(start_button.get('disabled'), '')  # Button should be disabled initially
        self.assertEqual(stop_button.get('style'), 'display: none;')
        self.assertEqual(start_button.text, 'Connect')
        self.assertEqual(stop_button.text, 'Disconnect')
        
        # Check recording controls
        start_recording = soup.find(id='start-recording')
        stop_recording = soup.find(id='stop-recording')
        self.assertIsNotNone(start_recording)
        self.assertIsNotNone(stop_recording)
    
    def test_static_assets(self):
        """Test that required static assets are served."""
        # Test camera stream JS
        response = self.client.get('/static/js/camera_stream.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'class CameraStream', response.data)
    
    def test_recording_endpoints(self):
        """Test recording API endpoints."""
        # Test start recording
        response = self.client.post('/api/v1/camera/record/start')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'recording started')
        
        # Test stop recording
        response = self.client.post('/api/v1/camera/record/stop')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'recording stopped')
    
    def test_error_responses(self):
        """Test error handling for API endpoints."""
        # Test invalid camera endpoint
        response = self.client.get('/api/v1/camera/invalid')
        self.assertEqual(response.status_code, 404)
        
        # Test invalid recording command
        response = self.client.post('/api/v1/camera/record/invalid')
        self.assertEqual(response.status_code, 404)
    
    def test_camera_initialization(self):
        """Test camera initialization endpoint."""
        # Test camera initialization
        response = self.client.post('/api/v1/camera/initialize/0')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Camera 0 initialized')

if __name__ == '__main__':
    unittest.main() 
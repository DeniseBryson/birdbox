import unittest
import tempfile
import shutil
import time
from pathlib import Path
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hardware.camera_mock import CameraMock
from src.utils.storage_manager import StorageManager

class TestCameraRecording(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage_manager = StorageManager(
            base_path=self.test_dir,
            storage_limit_gb=1.0,
            warning_threshold=0.85
        )
        
        # Initialize camera
        self.camera = CameraMock(resolution=(640, 480))
        self.camera.start()
        
    def tearDown(self):
        """Clean up after each test"""
        self.camera.stop()
        shutil.rmtree(self.test_dir)
        
    def test_camera_recording_cycle(self):
        """Test full recording cycle with camera"""
        # Start recording
        self.camera.start_recording()
        
        # Let it record for 2 seconds
        time.sleep(2)
        
        # Stop recording and get frames
        frames = self.camera.stop_recording()
        self.assertIsNotNone(frames)
        self.assertTrue(len(frames) > 0)
        
        # Save the recording
        filepath = self.storage_manager.save_recording(frames)
        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.exists())
        
        # Check the recording metadata
        recordings = self.storage_manager.get_recordings_list()
        self.assertEqual(len(recordings), 1)
        
        recording = recordings[0]
        self.assertTrue(recording['size_bytes'] > 0)
        # Check duration is reasonable (at least 1 second)
        duration = float(recording['duration'].rstrip('s'))
        self.assertTrue(duration >= 1.0, f"Duration {duration}s is too short")
        
    def test_camera_resolution_change(self):
        """Test recording with different resolutions"""
        resolutions = [(640, 480), (1280, 720)]
        
        for width, height in resolutions:
            # Change resolution
            self.camera.resolution = (width, height)
            
            # Record a short clip
            self.camera.start_recording()
            time.sleep(1)
            frames = self.camera.stop_recording()
            
            # Save and verify
            filepath = self.storage_manager.save_recording(frames)
            self.assertIsNotNone(filepath)
            
            # Verify frame dimensions
            recordings = self.storage_manager.get_recordings_list()
            self.assertTrue(len(recordings) > 0)
            
            # Check the first frame dimensions
            frame_height, frame_width = frames[0].shape[:2]
            self.assertEqual(frame_width, width)
            self.assertEqual(frame_height, height)
            
    def test_concurrent_operations(self):
        """Test recording while changing settings"""
        # Start recording
        self.camera.start_recording()
        
        # Change settings while recording
        self.camera.resolution = (1280, 720)
        self.camera.cycle_pattern()  # Change test pattern
        
        # Let it record the changes
        time.sleep(2)
        
        # Stop and save
        frames = self.camera.stop_recording()
        filepath = self.storage_manager.save_recording(frames)
        
        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.exists())
        
    def test_recording_status(self):
        """Test recording status tracking"""
        # Check initial state
        self.assertFalse(self.camera.is_recording)
        
        # Start recording
        self.camera.start_recording()
        self.assertTrue(self.camera.is_recording)
        
        # Record for at least 1 second to ensure frames
        time.sleep(1)
        
        # Stop recording
        frames = self.camera.stop_recording()
        self.assertFalse(self.camera.is_recording)
        self.assertTrue(len(frames) > 0, "No frames were recorded")
        
        # Save and verify
        filepath = self.storage_manager.save_recording(frames)
        self.assertIsNotNone(filepath, "Failed to save recording")
        self.assertTrue(filepath.exists(), "Recording file does not exist")
        
if __name__ == '__main__':
    unittest.main() 
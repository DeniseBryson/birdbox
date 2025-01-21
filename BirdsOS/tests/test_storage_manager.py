import unittest
import cv2
import numpy as np
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from src.utils.storage_manager import StorageManager
import time

class TestStorageManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.storage_manager = StorageManager(
            base_path=self.test_dir,
            storage_limit_gb=1.0,  # 1GB limit for testing
            warning_threshold=0.85
        )
        
        # Create some test frames
        self.test_frames = []
        for i in range(30):  # 1 second of video at 30fps
            # Create a frame with a timestamp and frame number
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                f'Frame {i} - {datetime.now()}',
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            self.test_frames.append(frame)
            
    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.test_dir)
        
    def test_save_and_read_recording(self):
        """Test saving a recording and reading it back"""
        # Save the test frames
        filepath = self.storage_manager.save_recording(self.test_frames)
        self.assertIsNotNone(filepath)
        self.assertTrue(filepath.exists())
        
        # Get the recordings list
        recordings = self.storage_manager.get_recordings_list()
        self.assertEqual(len(recordings), 1)
        
        # Verify recording metadata
        recording = recordings[0]
        self.assertTrue(recording['size_bytes'] > 0)
        self.assertEqual(recording['duration'], '1.0s')  # 30 frames at 30fps = 1 second
        
        # Verify video can be opened and read
        cap = cv2.VideoCapture(str(filepath))
        self.assertTrue(cap.isOpened())
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            
        cap.release()
        self.assertEqual(frame_count, 30)  # Should have 30 frames
        
    def test_delete_recording(self):
        """Test deleting a recording"""
        # Save a recording
        filepath = self.storage_manager.save_recording(self.test_frames)
        self.assertIsNotNone(filepath)
        
        # Get the recording ID
        recordings = self.storage_manager.get_recordings_list()
        self.assertEqual(len(recordings), 1)
        recording_id = recordings[0]['id']
        
        # Delete the recording
        success = self.storage_manager.delete_recording(recording_id)
        self.assertTrue(success)
        
        # Verify it's gone
        recordings = self.storage_manager.get_recordings_list()
        self.assertEqual(len(recordings), 0)
        self.assertFalse(filepath.exists())
        
    def test_cleanup_failed_recordings(self):
        """Test cleanup of failed/corrupt recordings"""
        # Create an empty file
        empty_file = self.storage_manager.recordings_path / "20250101_000000.avi"
        empty_file.touch()
        
        # Create a corrupt file
        corrupt_file = self.storage_manager.recordings_path / "20250101_000001.avi"
        with open(corrupt_file, 'wb') as f:
            f.write(b'Not a valid video file')
            
        # Run cleanup
        self.storage_manager.cleanup_failed_recordings()
        
        # Verify files are removed
        self.assertFalse(empty_file.exists())
        self.assertFalse(corrupt_file.exists())
        
    def test_storage_limits(self):
        """Test storage limits and warnings"""
        # Set a storage limit of 10KB for testing
        self.storage_manager.storage_limit = 10 * 1024  # 10KB
        
        # Create a large test frame that would exceed the limit
        large_frame = np.ones((50, 50, 3), dtype=np.uint8) * 255  # 7.5KB raw size
        large_frames = [large_frame] * 5  # 5 frames = ~15KB compressed
        
        # Try to save the recording
        filepath = self.storage_manager.save_recording(large_frames)
        self.assertIsNone(filepath, "Recording should fail due to size limit")
        
        # Create a small frame that will use ~85% of the limit
        small_frame = np.ones((16, 16, 3), dtype=np.uint8)  # 768 bytes raw size
        small_frames = [small_frame] * 5  # 5 frames = ~2KB compressed
        
        # Save the small recording
        filepath = self.storage_manager.save_recording(small_frames)
        self.assertIsNotNone(filepath, "Small recording should succeed")
        self.assertTrue(filepath.exists(), "Recording file should exist")
        
        # Get storage status
        status = self.storage_manager.get_storage_status()
        self.assertGreaterEqual(status['usage_percent'], 85.0, "Usage should be at least 85%")
        
        # Check warning - should be active since we used ~85%
        warning_active, warning_msg = self.storage_manager.check_storage_warning()
        self.assertTrue(warning_active, "Storage warning should be active")
        self.assertIn("85.0%", warning_msg, "Warning message should mention threshold")
        
    def test_get_recordings_metadata(self):
        """Test getting recording metadata"""
        # Set a higher storage limit for multiple recordings
        self.storage_manager.storage_limit = 20 * 1024  # 20KB
        
        # Save multiple recordings
        timestamps = []
        for i in range(3):
            # Create unique timestamp with 1 second gap
            timestamp = datetime.now()
            timestamps.append(timestamp)
            
            # Create test frames with timestamp
            frames = []
            for j in range(5):  # 5 frames is enough for testing
                frame = np.zeros((16, 16, 3), dtype=np.uint8)  # 768 bytes raw size
                cv2.putText(
                    frame,
                    f'{i}',  # Just the recording number
                    (2, 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.25,  # Tiny font
                    (255, 255, 255),
                    1
                )
                frames.append(frame)
            
            # Save recording
            filepath = self.storage_manager.save_recording(frames, timestamp)
            self.assertIsNotNone(filepath, f"Failed to save recording {i}")
            self.assertTrue(filepath.exists(), f"Recording file {i} does not exist")
            
            # Wait a bit between recordings
            time.sleep(0.1)
            
        # Get recordings list
        recordings = self.storage_manager.get_recordings_list()
        self.assertEqual(len(recordings), 3, f"Expected 3 recordings, got {len(recordings)}")
        
        # Verify they're sorted by timestamp (newest first)
        for i, recording in enumerate(recordings):
            expected_time = timestamps[-(i+1)].strftime("%Y-%m-%d %H:%M:%S")
            self.assertEqual(
                recording['timestamp'],
                expected_time,
                f"Recording {i} timestamp mismatch: {recording['timestamp']} != {expected_time}"
            )
            
            # Verify other metadata
            self.assertTrue(recording['size_bytes'] > 0, f"Recording {i} has no size")
            duration = float(recording['duration'].rstrip('s'))
            self.assertGreaterEqual(duration, 0.1, f"Recording {i} duration too short: {duration}s")
        
if __name__ == '__main__':
    unittest.main() 
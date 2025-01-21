import unittest
import cv2
import numpy as np
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hardware.camera import Camera

class TestMotionDetection(unittest.TestCase):
    def setUp(self):
        """Set up test camera instance"""
        self.camera = Camera(camera_id=0, resolution=(640, 480))
        
    def create_test_frame(self, color=(0, 0, 0)):
        """Create a test frame with given background color"""
        return np.full((480, 640, 3), color, dtype=np.uint8)
        
    def test_motion_detection_initialization(self):
        """Test motion detection parameters are properly initialized"""
        self.assertFalse(self.camera.motion_detected)
        self.assertIsNone(self.camera.prev_frame)
        self.assertEqual(self.camera.motion_threshold, 1000)
        self.assertEqual(self.camera.min_motion_area, 500)
        self.assertEqual(self.camera.motion_sensitivity, 25)
        
    def test_no_motion_detected(self):
        """Test that identical frames produce no motion"""
        frame1 = self.create_test_frame()
        frame2 = self.create_test_frame()
        
        # First frame sets reference
        self.assertFalse(self.camera.detect_motion(frame1))
        # Second identical frame should not detect motion
        self.assertFalse(self.camera.detect_motion(frame2))
        
    def test_motion_detected(self):
        """Test that different frames trigger motion detection"""
        # Create two different frames
        frame1 = self.create_test_frame((0, 0, 0))  # Black frame
        frame2 = frame1.copy()
        # Add a large white rectangle to second frame
        cv2.rectangle(frame2, (100, 100), (300, 300), (255, 255, 255), -1)
        
        # First frame sets reference
        self.assertFalse(self.camera.detect_motion(frame1))
        # Second frame should detect motion
        self.assertTrue(self.camera.detect_motion(frame2))
        
    def test_small_motion_ignored(self):
        """Test that motion smaller than min_area is ignored"""
        frame1 = self.create_test_frame((0, 0, 0))  # Black frame
        frame2 = frame1.copy()
        # Add a small white dot
        cv2.circle(frame2, (100, 100), 5, (255, 255, 255), -1)
        
        # First frame sets reference
        self.assertFalse(self.camera.detect_motion(frame1))
        # Small motion should not trigger detection
        self.assertFalse(self.camera.detect_motion(frame2))
        
    def test_sensitivity_adjustment(self):
        """Test motion detection with different sensitivity settings"""
        frame1 = self.create_test_frame((0, 0, 0))
        frame2 = frame1.copy()
        # Add a gray rectangle (subtle change)
        cv2.rectangle(frame2, (100, 100), (300, 300), (50, 50, 50), -1)
        
        # Test with high sensitivity
        self.camera.motion_sensitivity = 10
        self.assertFalse(self.camera.detect_motion(frame1))
        self.assertTrue(self.camera.detect_motion(frame2))
        
        # Test with low sensitivity
        self.camera.motion_sensitivity = 100
        self.assertFalse(self.camera.detect_motion(frame1))
        self.assertFalse(self.camera.detect_motion(frame2))
        
    def test_camera_info_includes_motion(self):
        """Test that camera info includes motion detection status"""
        info = self.camera.get_camera_info()
        self.assertIn('motion_detected', info)
        self.assertFalse(info['motion_detected'])

if __name__ == '__main__':
    unittest.main() 
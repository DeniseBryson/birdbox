"""
Mock camera implementation for development and testing
"""
import cv2
import numpy as np
import time
import threading
from queue import Queue
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger('BirdsOS')

class CameraMock:
    def __init__(self, resolution=(640, 480), fps=30):
        """Initialize mock camera with given resolution and fps"""
        self.resolution = resolution
        self.fps = fps
        self.is_running = False
        self.is_recording = False
        self.frame_buffer = Queue(maxsize=300)  # 10 seconds at 30fps
        self.recording_frames = []
        self.thread = None
        
        # Create a simple test pattern
        self.create_test_pattern()
        
        logger.info("Initialized Camera Mock")
        
    def create_test_pattern(self):
        """Create a test pattern image"""
        width, height = self.resolution
        self.test_pattern = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add grid lines
        for x in range(0, width, 50):
            cv2.line(self.test_pattern, (x, 0), (x, height), (50, 50, 50), 1)
        for y in range(0, height, 50):
            cv2.line(self.test_pattern, (0, y), (width, y), (50, 50, 50), 1)
            
        # Add center crosshair
        center_x, center_y = width // 2, height // 2
        cv2.line(self.test_pattern, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
        cv2.line(self.test_pattern, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)
        
        # Add resolution text
        text = f"{width}x{height}"
        cv2.putText(self.test_pattern, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add timestamp placeholder
        self.timestamp_pos = (10, height - 10)
        
    def start(self):
        """Start the camera thread"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._camera_thread)
            self.thread.daemon = True
            self.thread.start()
            
    def stop(self):
        """Stop the camera thread"""
        self.is_running = False
        if self.thread:
            self.thread.join()
        logger.info("Stopped mock camera feed")
        
    def _camera_thread(self):
        """Main camera thread that generates frames"""
        while self.is_running:
            frame = self.test_pattern.copy()
            
            # Add current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, self.timestamp_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add recording indicator
            if self.is_recording:
                cv2.circle(frame, (self.resolution[0] - 30, 30), 10, (0, 0, 255), -1)
            
            # Add simulated motion (moving dot)
            t = time.time()
            x = int(self.resolution[0]/2 + np.sin(t) * 100)
            y = int(self.resolution[1]/2 + np.cos(t) * 100)
            cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)
            
            # Store frame in buffer
            if self.frame_buffer.full():
                self.frame_buffer.get()
            self.frame_buffer.put(frame)
            
            # Store frame if recording
            if self.is_recording:
                self.recording_frames.append(frame)
                
            time.sleep(1/self.fps)
            
    def get_frame(self):
        """Get the latest frame"""
        if not self.frame_buffer.empty():
            return self.frame_buffer.get()
        return None
        
    def get_video_stream(self):
        """Generator function for video streaming"""
        while self.is_running:
            frame = self.get_frame()
            if frame is not None:
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                    
    def start_recording(self):
        """Start recording frames"""
        self.is_recording = True
        self.recording_frames = []
        
    def stop_recording(self):
        """Stop recording and return the recorded frames"""
        self.is_recording = False
        frames = self.recording_frames
        self.recording_frames = []
        logger.info("Stopped recording, buffer size: %d frames", len(frames))
        return frames
        
    @property
    def resolution(self):
        """Get current resolution"""
        return self._resolution
        
    @resolution.setter
    def resolution(self, value):
        """Set new resolution and recreate test pattern"""
        self._resolution = value
        self.create_test_pattern() 
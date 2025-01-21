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
from typing import Optional, Tuple, List
import queue
import math

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
        self.pattern_index = 0
        self.patterns = ['grid', 'circles', 'color_bars']
        self.motion_detected = False
        self.last_motion_pos = None
        self.frame_count = 0
        self.start_time = time.time()
        
        # Create test patterns
        self.create_test_patterns()
        
        logger.info("Initialized Camera Mock")
        
    def create_test_patterns(self):
        """Create test patterns for the mock camera"""
        width, height = self.resolution
        self.test_patterns = {}
        
        # Grid pattern
        grid = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(0, width, 50):
            cv2.line(grid, (i, 0), (i, height), (255, 255, 255), 1)
        for i in range(0, height, 50):
            cv2.line(grid, (0, i), (width, i), (255, 255, 255), 1)
        self.test_patterns['grid'] = grid
        
        # Circles pattern
        circles = np.zeros((height, width, 3), dtype=np.uint8)
        center = (width // 2, height // 2)
        for r in range(50, min(width, height) // 2, 50):
            cv2.circle(circles, center, r, (0, 255, 0), 2)
        self.test_patterns['circles'] = circles
        
        # Color bars pattern
        bars = np.zeros((height, width, 3), dtype=np.uint8)
        bar_width = width // 7
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 255, 255) # White
        ]
        for i, color in enumerate(colors):
            x1 = i * bar_width
            x2 = (i + 1) * bar_width
            bars[:, x1:x2] = color
        self.test_patterns['color_bars'] = bars
        
        self.patterns = list(self.test_patterns.keys())
        self.pattern_index = 0

    def add_overlay(self, frame):
        """Add timestamp and info overlay to frame"""
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add resolution
        cv2.putText(frame, f"{self.resolution[0]}x{self.resolution[1]}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add FPS
        if self.start_time:
            fps = self.frame_count / (time.time() - self.start_time)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Add recording indicator
        if self.is_recording:
            cv2.putText(frame, "REC", (frame.shape[1] - 100, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return frame

    def simulate_motion(self, frame):
        """Simulate motion in the frame"""
        # Add a moving dot
        t = time.time()
        x = int(self.resolution[0] / 2 + math.sin(t) * 100)
        y = int(self.resolution[1] / 2 + math.cos(t) * 100)
        cv2.circle(frame, (x, y), 10, (0, 0, 255), -1)
        
        # Detect if dot is in motion detection zone
        center_x = self.resolution[0] // 2
        center_y = self.resolution[1] // 2
        motion = abs(x - center_x) > 50 or abs(y - center_y) > 50
        
        return frame, motion
    
    def _camera_thread(self):
        """Main camera thread that generates frames"""
        self.start_time = time.time()
        self.frame_count = 0
        
        while self.is_running:
            try:
                # Get current test pattern and add motion
                frame = self.test_patterns[self.patterns[self.pattern_index]].copy()
                frame, motion = self.simulate_motion(frame)
                
                # Add overlays
                frame = self.add_overlay(frame)
                
                # Store frame in buffer
                try:
                    if self.frame_buffer.full():
                        self.frame_buffer.get_nowait()  # Remove oldest frame
                    self.frame_buffer.put_nowait(frame.copy())
                except queue.Full:
                    continue
                
                # Store frame if recording
                if self.is_recording:
                    self.recording_frames.append(frame.copy())
                
                self.frame_count += 1
                time.sleep(1.0 / self.fps)  # Control frame rate
                
            except Exception as e:
                logging.error(f"Error in camera thread: {str(e)}")
                time.sleep(0.1)  # Avoid tight loop on error
    
    def cycle_pattern(self):
        """Switch to next test pattern"""
        self.pattern_index = (self.pattern_index + 1) % len(self.patterns)
        return self.patterns[self.pattern_index]
        
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
        
    def get_frame(self):
        """Get the latest frame"""
        if not self.frame_buffer.empty():
            frame = self.frame_buffer.get()
            # Put the frame back if we're recording to keep it in buffer
            if self.is_recording:
                self.frame_buffer.put(frame)
            return frame
        return None
        
    def get_video_stream(self):
        """Generator function for video streaming"""
        while self.is_running:
            frame = self.get_frame()
            if frame is not None:
                try:
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                except Exception as e:
                    logger.error(f"Error encoding frame: {e}")
                    continue
                    
    def start_recording(self):
        """Start recording frames"""
        self.is_recording = True
        self.recording_frames = []
        logger.info("Started recording")
        
    def stop_recording(self):
        """Stop recording and return the recorded frames"""
        self.is_recording = False
        frames = self.recording_frames
        self.recording_frames = []
        logger.info(f"Stopped recording, buffer size: {len(frames)} frames")
        return frames if len(frames) > 0 else None
        
    @property
    def resolution(self):
        """Get current resolution"""
        return self._resolution
        
    @resolution.setter
    def resolution(self, value):
        """Set new resolution and recreate test pattern"""
        self._resolution = value
        self.create_test_patterns() 
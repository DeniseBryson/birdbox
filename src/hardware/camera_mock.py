import time
import math
import logging
import queue
import numpy as np
import cv2
from datetime import datetime
import threading

class CameraMock:
    def __init__(self, resolution=(640, 480), fps=30):
        self.resolution = resolution
        self.fps = fps
        self.is_running = False
        self.is_recording = False
        self.frame_buffer = queue.Queue(maxsize=10)
        self.recording_frames = []
        self.start_time = 0
        self.frame_count = 0
        self._thread = None

    def _camera_thread(self):
        """Main camera thread that generates frames"""
        self.start_time = time.time()
        self.frame_count = 0
        
        while self.is_running:
            try:
                # Create a test pattern frame
                frame = np.zeros(self.resolution + (3,), dtype=np.uint8)
                
                # Add timestamp and resolution text
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, f"{self.resolution[0]}x{self.resolution[1]}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Store frame in buffer
                try:
                    self.frame_buffer.put_nowait(frame.copy())
                except queue.Full:
                    self.frame_buffer.get_nowait()  # Remove oldest frame
                    self.frame_buffer.put_nowait(frame.copy())
                
                # Store frame if recording
                if self.is_recording:
                    self.recording_frames.append(frame.copy())
                
                self.frame_count += 1
                time.sleep(1.0 / self.fps)  # Control frame rate
                
            except Exception as e:
                logging.error(f"Error in camera thread: {str(e)}")
                time.sleep(0.1)  # Avoid tight loop on error

    def start(self):
        """Start the camera thread"""
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._camera_thread)
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        """Stop the camera thread"""
        if self.is_running:
            self.is_running = False
            if self._thread:
                self._thread.join(timeout=1.0)
                self._thread = None

    def record(self, is_recording):
        self.is_recording = is_recording

    def get_frame(self):
        return self.frame_buffer.get()

    def get_recording_frames(self):
        return self.recording_frames

    def get_frame_count(self):
        return self.frame_count

    def get_start_time(self):
        return self.start_time

    def get_resolution(self):
        return self.resolution

    def get_fps(self):
        return self.fps 
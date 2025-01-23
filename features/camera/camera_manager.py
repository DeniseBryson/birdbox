"""Camera management module for BirdsOS."""

import cv2
import numpy as np
from threading import Lock
import time
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class CameraManager:
    """Manages camera operations including streaming and recording."""
    
    def __init__(self):
        """Initialize camera manager."""
        self.camera = None
        self.is_initialized = False
        self.lock = Lock()
        self.resolution = (640, 480)  # Default resolution
        self.last_frame = None
        self.last_frame_time = 0
        self.frame_interval = 1.0 / 30  # Target 30 FPS
        self.device_id = None
        self.recording = False
        self.video_writer = None
        self.recordings_dir = 'recordings'
        
        # Create recordings directory if it doesn't exist
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)
    
    def initialize(self, device_id=0):
        """Initialize the camera with specified device ID."""
        with self.lock:
            if self.is_initialized and self.device_id == device_id:
                return True
            
            # Stop any existing camera
            if self.is_initialized:
                self.stop()
            
            try:
                self.device_id = device_id
                self.camera = cv2.VideoCapture(device_id)
                
                if not self.camera.isOpened():
                    raise RuntimeError(f"Failed to open camera {device_id}")
                
                # Set resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                
                # Set buffer size to minimize latency
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Set other optimizations
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                
                # Verify settings
                actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
                actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
                actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
                
                logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
                
                self.is_initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize camera: {str(e)}")
                self.stop()
                raise
    
    def get_frame(self):
        """Capture and return a single frame."""
        if not self.is_initialized:
            raise RuntimeError("Camera not initialized")
        
        current_time = time.time()
        if current_time - self.last_frame_time < self.frame_interval:
            return self.last_frame
        
        with self.lock:
            if not self.camera.isOpened():
                logger.error("Camera connection lost")
                self.stop()
                return None
            
            ret, frame = self.camera.read()
            if not ret:
                logger.error("Failed to capture frame")
                return None
            
            # Record frame if recording is active
            if self.recording and self.video_writer is not None:
                self.video_writer.write(frame)
            
            # Convert frame to JPEG with quality optimization
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]  # Balanced quality
            ret, jpeg = cv2.imencode('.jpg', frame, encode_params)
            if not ret:
                logger.error("Failed to encode frame")
                return None
            
            self.last_frame = jpeg
            self.last_frame_time = current_time
            return jpeg
    
    def start_recording(self):
        """Start recording video."""
        with self.lock:
            if not self.is_initialized:
                raise RuntimeError("Camera not initialized")
            
            if self.recording:
                return False
            
            try:
                # Create filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = os.path.join(self.recordings_dir, f'recording_{timestamp}.avi')
                
                # Initialize video writer
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.video_writer = cv2.VideoWriter(
                    filename,
                    fourcc,
                    30.0,  # FPS
                    (int(self.resolution[0]), int(self.resolution[1]))
                )
                
                self.recording = True
                logger.info(f"Started recording to {filename}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start recording: {str(e)}")
                self.recording = False
                self.video_writer = None
                raise
    
    def stop_recording(self):
        """Stop recording video."""
        with self.lock:
            if not self.recording:
                return False
            
            try:
                if self.video_writer is not None:
                    self.video_writer.release()
                    self.video_writer = None
                
                self.recording = False
                logger.info("Recording stopped")
                return True
                
            except Exception as e:
                logger.error(f"Failed to stop recording: {str(e)}")
                raise
            finally:
                self.recording = False
                self.video_writer = None
    
    def get_resolution(self):
        """Get current camera resolution."""
        if not self.is_initialized:
            return self.resolution
        
        with self.lock:
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return {
                'width': actual_width,
                'height': actual_height
            }
    
    def stop(self):
        """Stop and release the camera."""
        with self.lock:
            # Stop recording if active
            if self.recording:
                self.stop_recording()
            
            if self.is_initialized and self.camera is not None:
                try:
                    self.camera.release()
                except Exception as e:
                    logger.error(f"Error releasing camera: {str(e)}")
                finally:
                    self.is_initialized = False
                    self.camera = None
                    self.last_frame = None
                    self.last_frame_time = 0
                    self.device_id = None
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop() 
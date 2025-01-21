"""
Real camera implementation for BirdsOS
"""
import cv2
import logging
import threading
from queue import Queue
from datetime import datetime
from typing import List, Optional, Tuple
import time

logger = logging.getLogger('BirdsOS')

class Camera:
    def __init__(self, camera_id: int = 0, resolution: Tuple[int, int] = (1280, 720)):
        """
        Initialize camera
        
        Args:
            camera_id: Camera device ID (usually 0 for built-in, 1+ for external)
            resolution: Desired resolution (width, height)
        """
        self.camera_id = camera_id
        self._resolution = resolution
        self.is_running = False
        self.is_recording = False
        self.recording_frames = []
        self.frame_buffer = Queue(maxsize=30)  # 1 second buffer at 30fps
        self.frame_count = 0
        self.start_time = None
        self.thread = None
        self.cap = None
        self.fps = 30  # Default FPS
        self.last_frame_time = 0  # Track last successful frame read
        self.frame_timeout = 5.0  # Timeout in seconds for frame reading
        
        # Motion detection parameters
        self.motion_detected = False
        self.prev_frame = None
        self.motion_threshold = 1000  # Adjust based on sensitivity needs
        self.min_motion_area = 500  # Minimum contour area to be considered motion
        self.motion_sensitivity = 25  # Threshold for motion detection (0-255)
        
        logger.info(f"Initialized Camera (ID: {camera_id})")
        
    @staticmethod
    def list_cameras(max_attempts: int = 2) -> List[dict]:
        """
        List all available cameras
        
        Args:
            max_attempts: Maximum number of camera indices to check
            
        Returns:
            List of dicts with camera info (id, name, resolution)
        """
        cameras = []
        
        for i in range(max_attempts):
            cap = None
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Get camera info
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    name = f"Camera {i}"
                    
                    cameras.append({
                        "id": i,
                        "name": name,
                        "resolution": (width, height),
                        "status": "available"
                    })
                    logger.info(f"Found camera at index {i}: {width}x{height}")
                else:
                    logger.info(f"No camera available at index {i}")
            except Exception as e:
                logger.warning(f"Error checking camera at index {i}: {str(e)}")
            finally:
                if cap is not None:
                    cap.release()
                
        if not cameras:
            logger.warning("No cameras found. If using a mock environment, please ensure camera_mock.py is being used instead.")
            
        return cameras
        
    def start(self):
        """Start the camera thread"""
        if not self.is_running:
            try:
                if self.cap is None:  # Only create new capture if none exists
                    self.cap = cv2.VideoCapture(self.camera_id)
                
                if not self.cap.isOpened():
                    raise RuntimeError(f"Failed to open camera {self.camera_id}. Please check if the camera is connected and not in use by another application.")
                    
                # Set resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
                
                # Set FPS
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                
                # Test frame read
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    raise RuntimeError(f"Failed initial frame read from camera {self.camera_id}")
                
                self.is_running = True
                self.start_time = datetime.now().timestamp()
                self.last_frame_time = time.time()
                self.thread = threading.Thread(target=self._camera_thread)
                self.thread.daemon = True
                self.thread.start()
                logger.info(f"Started camera {self.camera_id} successfully")
            except Exception as e:
                logger.error(f"Failed to start camera {self.camera_id}: {str(e)}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                raise
            
    def stop(self):
        """Stop the camera thread"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)  # Wait up to 2 seconds for thread to finish
            if self.thread.is_alive():
                logger.warning("Camera thread did not terminate cleanly")
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info(f"Stopped camera {self.camera_id}")
        
    def detect_motion(self, frame) -> bool:
        """
        Detect motion in frame using frame differencing and contour detection
        
        Args:
            frame: Current frame to check for motion
            
        Returns:
            bool: True if motion detected, False otherwise
        """
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Apply Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize previous frame if needed
        if self.prev_frame is None:
            self.prev_frame = gray
            return False
            
        # Calculate absolute difference between current and previous frame
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        
        # Apply threshold to get binary image
        thresh = cv2.threshold(frame_delta, self.motion_sensitivity, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate thresholded image to fill in holes
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours in thresholded image
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check each contour
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_motion_area:
                motion_detected = True
                # Draw motion detection boxes (useful for debugging)
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Update previous frame
        self.prev_frame = gray
        
        return motion_detected

    def _camera_thread(self):
        """Main camera thread that reads frames from the camera"""
        self.start_time = time.time()
        self.frame_count = 0
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_running:
            try:
                # Check if we've exceeded frame timeout
                if time.time() - self.last_frame_time > self.frame_timeout:
                    logger.error(f"No frames received for {self.frame_timeout} seconds")
                    break
                
                # Read frame from camera
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    consecutive_errors += 1
                    logger.error(f"Failed to read frame (attempt {consecutive_errors}/{max_consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive frame read failures")
                        break
                    time.sleep(0.1)
                    continue
                
                # Reset error counter on successful frame read
                consecutive_errors = 0
                self.last_frame_time = time.time()
                
                # Detect motion
                self.motion_detected = self.detect_motion(frame)
                if self.motion_detected:
                    logger.debug("Motion detected")
                    
                # Store frame in buffer
                if self.frame_buffer.full():
                    try:
                        self.frame_buffer.get_nowait()
                    except:
                        pass
                try:
                    self.frame_buffer.put_nowait(frame.copy())
                except:
                    pass
                    
                # Store frame if recording
                if self.is_recording:
                    self.recording_frames.append(frame.copy())
                    
                self.frame_count += 1
                time.sleep(1/self.fps)
            except Exception as e:
                logger.error(f"Error in camera thread: {e}")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors in camera thread")
                    break
                continue
        
        # Clean up if thread exits
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.warning("Camera thread stopped")
        
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
        logger.info("Started recording")
        
    def stop_recording(self):
        """Stop recording and return the recorded frames"""
        self.is_recording = False
        frames = self.recording_frames
        self.recording_frames = []
        logger.info(f"Stopped recording, buffer size: {len(frames)} frames")
        return frames if frames else None
        
    @property
    def resolution(self):
        """Get current resolution"""
        return self._resolution
        
    @resolution.setter
    def resolution(self, value):
        """Set new resolution"""
        self._resolution = value
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, value[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, value[1])
            
    def get_camera_info(self) -> dict:
        """Get camera information and status"""
        fps = self.frame_count / (datetime.now().timestamp() - self.start_time) if self.start_time else 0
        return {
            "id": self.camera_id,
            "resolution": self._resolution,
            "fps": fps,
            "is_recording": self.is_recording,
            "motion_detected": self.motion_detected,
            "frame_count": self.frame_count,
            "status": "active" if self.is_running else "stopped"
        } 
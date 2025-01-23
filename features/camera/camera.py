"""
Core camera functionality for BirdsOS
"""
import cv2
import logging
import os
from datetime import datetime
from typing import Optional, Tuple, List, Dict

logger = logging.getLogger(__name__)

class Camera:
    """Handles core camera operations"""
    
    def __init__(self, camera_id: int = 0):
        """Initialize camera with specified ID
        
        Args:
            camera_id: ID of the camera device to use
        """
        self.camera_id = camera_id
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_width = 1280  # Default resolution
        self.frame_height = 720
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.recording_path: Optional[str] = None
        
    def start(self) -> bool:
        """Start the camera
        
        Returns:
            bool: True if camera started successfully
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}")
                return False
                
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.is_running = True
            logger.info(f"Camera {self.camera_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera: {str(e)}")
            return False
            
    def stop(self) -> None:
        """Stop the camera"""
        if self.video_writer is not None:
            self.stop_recording()
            
        if self.cap is not None:
            self.cap.release()
            self.is_running = False
            logger.info(f"Camera {self.camera_id} stopped")
            
    def get_frame(self) -> Tuple[bool, Optional[bytes]]:
        """Get current frame from camera
        
        Returns:
            Tuple[bool, Optional[bytes]]: Success flag and frame data
        """
        if not self.is_running or self.cap is None:
            return False, None
            
        ret, frame = self.cap.read()
        if not ret:
            return False, None
            
        # Write frame to video if recording
        if self.video_writer is not None:
            self.video_writer.write(frame)
            
        # Convert frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            return False, None
            
        return True, buffer.tobytes()
        
    def get_camera_info(self) -> Dict:
        """Get camera information
        
        Returns:
            Dict: Camera information including resolution and status
        """
        return {
            'id': self.camera_id,
            'resolution': (self.frame_width, self.frame_height),
            'is_running': self.is_running,
            'status': 'active' if self.is_running else 'stopped',
            'is_recording': self.video_writer is not None
        }
        
    def start_recording(self) -> bool:
        """Start recording video
        
        Returns:
            bool: True if recording started successfully
        """
        if not self.is_running:
            logger.error("Cannot start recording: Camera not running")
            return False
            
        if self.video_writer is not None:
            logger.warning("Recording already in progress")
            return True
            
        try:
            # Create recordings directory if it doesn't exist
            os.makedirs('recordings', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.recording_path = f'recordings/video_{timestamp}.mp4'
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                self.recording_path,
                fourcc,
                30.0,  # FPS
                (self.frame_width, self.frame_height)
            )
            
            logger.info(f"Started recording to {self.recording_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            self.video_writer = None
            self.recording_path = None
            return False
            
    def stop_recording(self) -> bool:
        """Stop recording video
        
        Returns:
            bool: True if recording stopped successfully
        """
        if self.video_writer is None:
            logger.warning("No recording in progress")
            return True
            
        try:
            self.video_writer.release()
            logger.info(f"Stopped recording to {self.recording_path}")
            self.video_writer = None
            self.recording_path = None
            return True
            
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            return False
        
    @staticmethod
    def list_cameras(max_cameras: int = 5) -> List[Dict]:
        """List available cameras
        
        Args:
            max_cameras: Maximum number of cameras to check
            
        Returns:
            List[Dict]: List of available cameras with their info
        """
        available_cameras = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.release()
                available_cameras.append({
                    'id': i,
                    'name': f'Camera {i}'
                })
        return available_cameras
        
    def __del__(self):
        """Cleanup on deletion"""
        self.stop() 
"""
Camera manager for BirdsOS
Handles camera lifecycle and provides high-level camera operations
"""
import logging
from typing import Optional, Dict
from .camera import Camera

logger = logging.getLogger(__name__)

class CameraManager:
    """Manages camera operations and lifecycle"""
    
    def __init__(self):
        """Initialize camera manager"""
        self._camera: Optional[Camera] = None
        self._active_camera_id: Optional[int] = None
        self._is_recording: bool = False
        
    def initialize_camera(self, camera_id: int = 0) -> bool:
        """Initialize and start a camera
        
        Args:
            camera_id: ID of the camera to initialize
            
        Returns:
            bool: True if camera initialized successfully
        """
        # Stop existing camera if any
        if self._camera is not None:
            self.stop_camera()
            
        try:
            self._camera = Camera(camera_id)
            if self._camera.start():
                self._active_camera_id = camera_id
                logger.info(f"Camera {camera_id} initialized")
                return True
            return False
        except Exception as e:
            logger.error(f"Error initializing camera: {str(e)}")
            return False
            
    def stop_camera(self) -> None:
        """Stop the active camera"""
        if self._camera is not None:
            if self._is_recording:
                self.stop_recording()
            self._camera.stop()
            self._camera = None
            self._active_camera_id = None
            logger.info("Camera stopped")
            
    def get_camera_status(self) -> Dict:
        """Get current camera status
        
        Returns:
            Dict: Camera status information
        """
        if self._camera is None:
            return {
                'active_camera': None,
                'status': 'inactive',
                'available_cameras': Camera.list_cameras()
            }
            
        return {
            'active_camera': self._active_camera_id,
            'status': 'active' if self._camera.is_running else 'stopped',
            'camera_info': self._camera.get_camera_info(),
            'available_cameras': Camera.list_cameras(),
            'is_recording': self._is_recording
        }
        
    def get_frame(self):
        """Get current frame from active camera"""
        if self._camera is None:
            return False, None
        return self._camera.get_frame()
        
    def start_recording(self) -> bool:
        """Start recording from the active camera
        
        Returns:
            bool: True if recording started successfully
        """
        if self._camera is None:
            logger.error("Cannot start recording: No active camera")
            return False
            
        if self._is_recording:
            logger.warning("Recording already in progress")
            return True
            
        try:
            if self._camera.start_recording():
                self._is_recording = True
                logger.info("Recording started")
                return True
            return False
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            return False
            
    def stop_recording(self) -> bool:
        """Stop recording from the active camera
        
        Returns:
            bool: True if recording stopped successfully
        """
        if self._camera is None:
            logger.error("Cannot stop recording: No active camera")
            return False
            
        if not self._is_recording:
            logger.warning("No recording in progress")
            return True
            
        try:
            if self._camera.stop_recording():
                self._is_recording = False
                logger.info("Recording stopped")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            return False
        
    def __del__(self):
        """Cleanup on deletion"""
        self.stop_camera() 
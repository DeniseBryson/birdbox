"""WebSocket routes for camera streaming in BirdsOS."""

import json
import time
import logging
from flask import Blueprint
from flask_sock import Sock
from features.camera.camera_manager import CameraManager

# Configure logging
logger = logging.getLogger(__name__)

# Create WebSocket blueprint
ws_bp = Blueprint('ws', __name__)
sock = Sock()

@sock.route('/api/v1/camera/stream')
def stream(ws):
    """Handle WebSocket connection for camera streaming."""
    camera = None
    try:
        # Initialize camera
        camera = CameraManager()
        camera.initialize()
        logger.info("Camera initialized successfully")
        
        # Send initial status
        ws.send(json.dumps({
            'type': 'status',
            'status': 'streaming',
            'resolution': camera.get_resolution()
        }))
        
        # Stream frames
        while True:
            try:
                frame = camera.get_frame()
                if frame is not None:
                    # Convert frame to Latin1 string for WebSocket transmission
                    frame_str = frame.tobytes().decode('latin1')
                    ws.send(json.dumps({
                        'type': 'frame',
                        'data': frame_str
                    }))
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                logger.error(f"Frame error: {str(e)}")
                ws.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
                break
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        ws.send(json.dumps({
            'type': 'error',
            'message': f'Failed to initialize camera: {str(e)}'
        }))
    finally:
        # Cleanup
        if camera:
            try:
                camera.stop()
                logger.info("Camera stopped")
            except Exception as e:
                logger.error(f"Error stopping camera: {str(e)}")
        logger.info("Stream connection closed") 
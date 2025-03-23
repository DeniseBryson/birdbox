"""
WebSocket handler for camera streaming
"""
import logging
import json
from flask_sock import Sock
from .manager import CameraManager

logger = logging.getLogger(__name__)
sock = Sock()

@sock.route('/api/v1/camera/stream')
def stream(ws):
    """Handle camera stream WebSocket connection"""
    camera_manager = CameraManager()
    
    try:
        # Initialize camera
        if not camera_manager.initialize_camera():
            ws.send(json.dumps({
                'type': 'error',
                'message': 'Failed to initialize camera'
            }))
            return
            
        # Send initial status
        ws.send(json.dumps({
            'type': 'status',
            'status': 'streaming',
            'resolution': camera_manager._camera.get_camera_info()['resolution']
        }))
        
        # Stream frames
        while True:
            success, frame = camera_manager.get_frame()
            if not success:
                ws.send(json.dumps({
                    'type': 'error',
                    'message': 'Failed to capture frame'
                }))
                break
                
            # Send frame data
            ws.send(json.dumps({
                'type': 'frame',
                'data': frame.decode('latin1')  # Convert bytes to string for JSON
            }))
            
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        ws.send(json.dumps({
            'type': 'error',
            'message': str(e)
        }))
        
    finally:
        # Cleanup
        camera_manager.stop_camera()
        logger.info("Stream connection closed") 
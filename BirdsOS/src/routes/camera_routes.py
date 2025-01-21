"""
Camera-related routes for BirdsOS
"""
from flask import Blueprint, render_template, jsonify, request, Response
from src.hardware.camera import Camera
from src.hardware.camera_mock import CameraMock
from src.utils.logger import setup_logger
import time

# Initialize blueprint and logger
camera_bp = Blueprint('camera', __name__)
logger = setup_logger()

# Global camera instance
camera = None

@camera_bp.route('/camera')
def camera_page():
    try:
        available_cameras = Camera.list_cameras()
        if not available_cameras:
            # If no physical cameras, add mock camera
            available_cameras = [{
                "id": 0,
                "name": "Mock Camera",
                "resolution": (640, 480),
                "status": "available"
            }]
        return render_template('camera.html', cameras=available_cameras)
    except Exception as e:
        logger.error(f"Error loading camera page: {e}")
        return render_template('camera.html', cameras=[])

@camera_bp.route('/api/cameras')
def list_cameras():
    """List all available cameras"""
    try:
        cameras = Camera.list_cameras()
        if not cameras:
            # If no physical cameras, add mock camera
            cameras = [{
                "id": 0,
                "name": "Mock Camera",
                "resolution": (640, 480),
                "status": "available"
            }]
        return jsonify(cameras)
    except Exception as e:
        logger.error(f"Error listing cameras: {e}")
        return jsonify({"error": str(e)}), 500

@camera_bp.route('/api/camera/select', methods=['POST'])
def select_camera():
    """Select and initialize a camera"""
    global camera
    
    try:
        data = request.get_json()
        if not data or 'camera_id' not in data:
            return jsonify({
                "error": "Missing camera_id",
                "status": "error"
            }), 400
            
        camera_id = data['camera_id']
        
        # Stop existing camera if any and it's a different camera
        if camera and camera.camera_id != camera_id:
            camera.stop()
            camera = None
        
        try:
            # Initialize new camera only if needed
            if not camera:
                # Try to initialize physical camera first
                physical_cameras = Camera.list_cameras()
                if physical_cameras and any(c['id'] == camera_id for c in physical_cameras):
                    camera = Camera(camera_id=camera_id)
                else:
                    # If no physical camera available or requested, use mock
                    logger.info("Using mock camera implementation")
                    camera = CameraMock()
            
            # Start camera if not running
            if not camera.is_running:
                camera.start()
                
            return jsonify({
                "status": "success",
                "camera": camera.get_camera_info()
            })
        except Exception as e:
            if camera:
                try:
                    camera.stop()
                except:
                    pass
                camera = None
            return jsonify({
                "error": f"Failed to initialize camera: {str(e)}",
                "status": "error"
            }), 400
            
    except Exception as e:
        logger.error(f"Error in camera selection: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@camera_bp.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if not camera:
        return "No camera selected", 400
    return Response(
        camera.get_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@camera_bp.route('/api/camera/status')
def camera_status():
    """Get current camera status"""
    if camera is None:
        return jsonify({
            "error": "No camera selected",
            "status": "error"
        }), 400
        
    try:
        status_data = {
            "fps": camera.frame_count / (time.time() - camera.start_time) if camera.start_time else 0,
            "resolution": camera.resolution,
            "is_recording": int(camera.is_recording),
            "status": "active" if camera.is_running else "stopped"
        }
        
        # Add mock-specific fields if available
        if hasattr(camera, 'motion_detected'):
            status_data['motion_detected'] = int(camera.motion_detected)
        if hasattr(camera, 'patterns') and hasattr(camera, 'pattern_index'):
            status_data['pattern'] = camera.patterns[camera.pattern_index]
            
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@camera_bp.route('/api/camera/settings', methods=['POST'])
def update_camera_settings():
    """Update camera settings"""
    if not camera:
        return jsonify({"error": "No camera selected"}), 400
    try:
        data = request.get_json()
        if 'resolution' in data:
            camera.resolution = tuple(data['resolution'])
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error updating camera settings: {e}")
        return jsonify({"error": str(e)}), 500

@camera_bp.route('/api/camera/record/start', methods=['POST'])
def start_recording():
    """Start recording from camera"""
    if camera is None:
        return jsonify({
            "error": "No camera selected",
            "status": "error"
        }), 400
        
    try:
        if not camera.is_running:
            return jsonify({
                "error": "Camera is not running",
                "status": "error"
            }), 400
            
        if camera.is_recording:
            return jsonify({
                "error": "Recording already in progress",
                "status": "error"
            }), 400
            
        camera.start_recording()
        
        # Verify recording started successfully
        if not camera.is_recording:
            return jsonify({
                "error": "Failed to start recording",
                "status": "error"
            }), 500
            
        return jsonify({
            "status": "success",
            "message": "Recording started"
        })
    except Exception as e:
        logger.error(f"Error starting recording: {e}")
        # Ensure recording is stopped on error
        try:
            camera.stop_recording()
        except:
            pass
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@camera_bp.route('/api/camera/record/stop', methods=['POST'])
def stop_recording():
    """Stop recording and save video"""
    if camera is None:
        return jsonify({
            "error": "No camera selected",
            "status": "error"
        }), 400
        
    try:
        if not camera.is_recording:
            return jsonify({
                "error": "No recording in progress",
                "status": "error"
            }), 400
            
        frames = camera.stop_recording()
        if not frames:
            return jsonify({
                "error": "No frames recorded",
                "status": "error"
            }), 400
            
        # Verify recording stopped successfully
        if camera.is_recording:
            return jsonify({
                "error": "Failed to stop recording",
                "status": "error"
            }), 500
            
        # Save recording
        try:
            if len(frames) < 1:
                return jsonify({
                    "error": "Recording contains no frames",
                    "status": "error"
                }), 400
                
            from app import storage_manager  # Import here to avoid circular import
            path = storage_manager.save_recording(frames)
            return jsonify({
                "status": "success",
                "path": str(path),  # Convert PosixPath to string
                "frame_count": len(frames)
            })
        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            return jsonify({
                "error": f"Failed to save recording: {e}",
                "status": "error"
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping recording: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@camera_bp.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """Stop the current camera"""
    global camera
    try:
        if camera:
            camera.stop()
            camera = None
            return jsonify({
                "status": "success",
                "message": "Camera stopped"
            })
        return jsonify({
            "status": "success",
            "message": "No camera was running"
        })
    except Exception as e:
        logger.error(f"Error stopping camera: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500 
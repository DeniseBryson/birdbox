"""
Camera routes for BirdsOS
"""
from flask import Blueprint, jsonify, render_template, current_app, g
from .manager import CameraManager

# Create blueprint
camera_bp = Blueprint('camera', __name__)

def get_camera_manager():
    """Get or create camera manager instance."""
    if 'camera_manager' not in g:
        g.camera_manager = CameraManager()
    return g.camera_manager

@camera_bp.teardown_app_request
def teardown_camera_manager(exception):
    """Clean up camera manager after request."""
    camera_manager = g.pop('camera_manager', None)
    if camera_manager is not None:
        camera_manager.stop_camera()

@camera_bp.route('/camera/')
def camera_page():
    """Render camera control page."""
    return render_template('camera.html')

@camera_bp.route('/api/v1/camera/status')
def get_camera_status():
    """Get camera status"""
    return jsonify(get_camera_manager().get_camera_status())

@camera_bp.route('/api/v1/camera/initialize/<int:camera_id>', methods=['POST'])
def initialize_camera(camera_id):
    """Initialize camera with given ID"""
    success = get_camera_manager().initialize_camera(camera_id)
    if success:
        return jsonify({
            'status': 'success',
            'message': f'Camera {camera_id} initialized'
        })
    return jsonify({
        'status': 'error',
        'message': f'Failed to initialize camera {camera_id}'
    }), 500

@camera_bp.route('/api/v1/camera/stop', methods=['POST'])
def stop_camera():
    """Stop active camera"""
    get_camera_manager().stop_camera()
    return jsonify({
        'status': 'success',
        'message': 'Camera stopped'
    })

@camera_bp.route('/api/v1/camera/record/start', methods=['POST'])
def start_recording():
    """Start camera recording."""
    camera_manager = get_camera_manager()
    
    try:
        if camera_manager.start_recording():
            return jsonify({
                'status': 'recording started'
            })
        return jsonify({
            'status': 'error',
            'message': 'Failed to start recording'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@camera_bp.route('/api/v1/camera/record/stop', methods=['POST'])
def stop_recording():
    """Stop camera recording."""
    camera_manager = get_camera_manager()
    
    try:
        if camera_manager.stop_recording():
            return jsonify({
                'status': 'recording stopped'
            })
        return jsonify({
            'status': 'error',
            'message': 'Failed to stop recording'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 
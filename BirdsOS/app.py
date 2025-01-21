"""
BirdsOS - Main Application
"""
from flask import Flask, render_template, jsonify, request, Response, send_file
from src.utils.logger import setup_logger
from src.utils.storage_manager import StorageManager
from src.hardware import GPIO
from src.routes.camera_routes import camera_bp
from src.routes.system_routes import system_bp
from config.default import *
import time
import os
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.default')
logger = setup_logger()

# Initialize storage manager
storage_manager = StorageManager(
    base_path=Path('data/recordings'),
    storage_limit_gb=10.0,
    warning_threshold=0.85
)

# Clean up any failed recordings on startup
storage_manager.cleanup_failed_recordings()

# Initialize GPIO pins
GPIO.setmode(GPIO.BCM)
# Set up monitored pins
MONITORED_PINS = {
    18: GPIO.OUT,  # Motor 1
    23: GPIO.OUT,  # Motor 2
    24: GPIO.IN,   # Optical Gate 1
    25: GPIO.IN    # Optical Gate 2
}
for pin, mode in MONITORED_PINS.items():
    GPIO.setup(pin, mode)
    logger.info(f"Initialized GPIO pin {pin} in {mode} mode")

# Register blueprints
app.register_blueprint(camera_bp)
app.register_blueprint(system_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gpio')
def gpio_simulator():
    """GPIO Simulator page"""
    return render_template('gpio_simulator.html')

@app.route('/api/storage/status')
def storage_status():
    """Get storage status"""
    try:
        status = storage_manager.get_storage_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting storage status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/camera/recordings')
def list_recordings():
    """List all recordings"""
    try:
        recordings = storage_manager.get_recordings_list()
        return jsonify({
            "status": "success",
            "recordings": recordings
        })
    except Exception as e:
        logger.error(f"Error listing recordings: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/camera/recordings/<recording_id>/download')
def download_recording(recording_id):
    """Download a specific recording"""
    try:
        recordings = storage_manager.get_recordings_list()
        recording = next((r for r in recordings if r['id'] == recording_id), None)
        
        if not recording:
            return jsonify({
                "error": "Recording not found",
                "status": "error"
            }), 404
            
        file_path = recording['path']
        if not os.path.exists(file_path):
            return jsonify({
                "error": "Recording file not found",
                "status": "error"
            }), 404
            
        return send_file(
            file_path,
            mimetype='video/x-msvideo',
            as_attachment=True,
            download_name=f"{recording_id}.avi"
        )
    except Exception as e:
        logger.error(f"Error downloading recording: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/camera/recordings/<recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    """Delete a specific recording"""
    try:
        recordings = storage_manager.get_recordings_list()
        recording = next((r for r in recordings if r['id'] == recording_id), None)
        
        if not recording:
            return jsonify({
                "error": "Recording not found",
                "status": "error"
            }), 404
            
        storage_manager.delete_recording(recording_id)
        return jsonify({
            "status": "success",
            "message": f"Recording {recording_id} deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting recording: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/gpio/status')
def gpio_status():
    """Get GPIO pin status"""
    try:
        status = GPIO.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting GPIO status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/gpio/trigger', methods=['POST'])
def gpio_trigger():
    """Trigger a GPIO pin state change"""
    try:
        data = request.get_json()
        pin = data.get('pin')
        state = data.get('state')
        
        if pin is None or state is None:
            return jsonify({
                "error": "Missing pin or state in request",
                "status": "error"
            }), 400
            
        if pin not in MONITORED_PINS:
            return jsonify({
                "error": f"Invalid pin {pin}",
                "status": "error"
            }), 500
            
        GPIO.trigger_input(pin, state)
        return jsonify({
            "status": "success",
            "message": f"Pin {pin} set to {state}"
        })
    except Exception as e:
        logger.error(f"Error triggering GPIO pin: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    logger.info("Starting BirdsOS...")
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    except KeyboardInterrupt:
        logger.info("Shutting down BirdsOS...")
    except Exception as e:
        logger.error(f"Error running BirdsOS: {e}")
    finally:
        # Clean up GPIO
        GPIO.cleanup()

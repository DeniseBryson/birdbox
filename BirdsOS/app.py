"""
BirdsOS - Main Application
"""
from flask import Flask, render_template, jsonify, request, Response
from src.utils.logger import setup_logger
from src.hardware import GPIO
from src.hardware.camera_mock import CameraMock
from config.default import *

app = Flask(__name__)
app.config.from_object('config.default')
logger = setup_logger()

# Initialize camera
camera = CameraMock(resolution=CAMERA_RESOLUTION)
camera.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gpio')
def gpio_simulator():
    return render_template('gpio_simulator.html')

@app.route('/camera')
def camera_simulator():
    return render_template('camera_simulator.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(camera.get_video_stream(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/record/start', methods=['POST'])
def start_recording():
    """Start recording video buffer"""
    try:
        camera.start_recording()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error starting recording: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/camera/record/stop', methods=['POST'])
def stop_recording():
    """Stop recording and save buffer"""
    try:
        frames = camera.stop_recording()
        # TODO: Save frames to file
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/camera/settings', methods=['POST'])
def update_camera_settings():
    """Update camera settings"""
    try:
        data = request.get_json()
        resolution = data.get('resolution')
        if resolution:
            camera.resolution = tuple(resolution)
            return jsonify({"status": "success"})
        return jsonify({
            "status": "error",
            "message": "Invalid settings"
        }), 400
    except Exception as e:
        logger.error(f"Error updating camera settings: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/camera/recordings')
def get_recordings():
    """Get list of recordings"""
    # TODO: Implement actual recording storage
    return jsonify({
        "recordings": [
            {
                "id": "demo-1",
                "timestamp": "2024-01-19 12:00:00",
                "duration": 30,
                "size": "15 MB"
            }
        ]
    })

@app.route('/api/gpio/status')
def gpio_status():
    """Get the current status of all monitored GPIO pins"""
    pins = {}
    for pin in [18, 23, 24, 25]:  # Motor and sensor pins
        pins[pin] = GPIO.get_pin_state(pin)
    return jsonify({"pins": pins})

@app.route('/api/gpio/trigger', methods=['POST'])
def gpio_trigger():
    """Trigger a GPIO input pin (simulation only)"""
    try:
        data = request.get_json()
        pin = data.get('pin')
        state = data.get('state')
        
        if pin is None or state is None:
            return jsonify({
                "status": "error",
                "message": "Pin and state are required"
            }), 400
            
        GPIO.trigger_input(pin, state)
        return jsonify({"status": "success"})
            
    except Exception as e:
        logger.error(f"Error triggering GPIO: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/status')
def status():
    # TODO: Implement status endpoint
    return {'status': 'operational'}

if __name__ == '__main__':
    logger.info("Starting BirdsOS...")
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    finally:
        camera.stop()  # Ensure camera is stopped when app exits

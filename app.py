# Initialize camera with None - will be set when a camera is selected
camera = None

@app.route('/api/camera/select/<int:camera_id>', methods=['POST'])
def select_camera(camera_id):
    """Select a camera by ID"""
    global camera
    camera = None  # Reset camera before attempting to initialize new one
    try:
        camera = Camera(camera_id)
        camera.start()
        return jsonify({"status": "success", "message": f"Selected camera {camera_id}"})
    except Exception as e:
        logging.error(f"Error selecting camera {camera_id}: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/camera/record/start', methods=['POST'])
def start_recording():
    """Start recording from camera"""
    global camera
    if camera is None:
        return jsonify({"error": "No camera selected", "status": "error"}), 400
    
    try:
        camera.start_recording()
        return jsonify({"status": "success", "message": "Recording started"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500 
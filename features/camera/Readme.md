# Camera Feature Documentation

## Overview
The camera feature provides functionality for camera control, live streaming, and video recording in BirdsOS.

## API Endpoints

### Status and Control
- `GET /api/v1/camera/status`
  - Returns camera status and available devices
  - Response: 
    ```json
    {
      "active_camera": 0,
      "status": "active",
      "camera_info": {
        "id": 0,
        "resolution": [1280, 720],
        "is_running": true,
        "status": "active"
      },
      "available_cameras": [
        {"id": 0, "status": "available"}
      ]
    }
    ```

- `POST /api/v1/camera/initialize/<camera_id>`
  - Initialize and start a specific camera
  - Response (success):
    ```json
    {
      "status": "success",
      "message": "Camera {id} initialized"
    }
    ```
  - Response (error):
    ```json
    {
      "status": "error",
      "message": "Failed to initialize camera {id}"
    }
    ```

- `POST /api/v1/camera/stop`
  - Stop the currently active camera
  - Response:
    ```json
    {
      "status": "success",
      "message": "Camera stopped"
    }
    ```

## Technical Details

### Camera Class
The `Camera` class provides low-level camera operations:
- Device initialization
- Frame capture
- Status monitoring
- Device enumeration

### Camera Manager
The `CameraManager` handles:
- Camera lifecycle management
- High-level operations
- Status tracking
- Resource cleanup

## Dependencies
- OpenCV (`opencv-python==4.9.0.80`)
- NumPy (`numpy<2.0`)
- Flask for API endpoints

## Testing
All components are tested with:
- Unit tests for Camera class
- Unit tests for CameraManager
- Integration tests for routes
- Mocked hardware for reliable testing 
# Camera Documentation

## Overview
The BirdsOS camera system provides a complete solution for camera management, including camera selection, video streaming, recording, and motion detection. The system includes both a REST API for programmatic control and a web-based UI for user interaction.

## API Endpoints

### Camera Management

#### List Available Cameras
- **Endpoint**: `GET /api/cameras`
- **Response**: List of available cameras with their properties
```json
[
    {
        "id": 0,
        "name": "Camera 0",
        "resolution": [1280, 720],
        "status": "available"
    }
]
```

#### Select Camera
- **Endpoint**: `POST /api/camera/select`
- **Body**:
```json
{
    "camera_id": 0
}
```
- **Response**: Camera information and status
```json
{
    "status": "success",
    "camera": {
        "id": 0,
        "resolution": [1280, 720],
        "status": "active"
    }
}
```

#### Stop Camera
- **Endpoint**: `POST /api/camera/stop`
- **Response**: Success message
```json
{
    "status": "success",
    "message": "Camera stopped"
}
```

#### Get Camera Status
- **Endpoint**: `GET /api/camera/status`
- **Response**: Current camera status
```json
{
    "fps": 15.32,
    "resolution": [1280, 720],
    "is_recording": false,
    "motion_detected": false,
    "status": "active"
}
```

#### Update Camera Settings
- **Endpoint**: `POST /api/camera/settings`
- **Body**:
```json
{
    "resolution": [1920, 1080]
}
```
- **Response**: Success status
```json
{
    "status": "success"
}
```

### Recording Management

#### Start Recording
- **Endpoint**: `POST /api/camera/record/start`
- **Response**: Success status
```json
{
    "status": "success",
    "message": "Recording started"
}
```

#### Stop Recording
- **Endpoint**: `POST /api/camera/record/stop`
- **Response**: Recording information
```json
{
    "status": "success",
    "path": "data/recordings/20250120_173757.avi",
    "frame_count": 106
}
```

#### List Recordings
- **Endpoint**: `GET /api/camera/recordings`
- **Response**: List of available recordings
```json
{
    "status": "success",
    "recordings": [
        {
            "id": "20250120_173757",
            "filename": "20250120_173757.avi",
            "path": "data/recordings/20250120_173757.avi",
            "timestamp": "2025-01-20 17:37:57",
            "duration": "3.5s",
            "size": "4.1MB"
        }
    ]
}
```

#### Download Recording
- **Endpoint**: `GET /api/camera/recordings/{recording_id}/download`
- **Response**: Video file download

#### Delete Recording
- **Endpoint**: `DELETE /api/camera/recordings/{recording_id}`
- **Response**: Success message
```json
{
    "status": "success",
    "message": "Recording deleted successfully"
}
```

### Storage Management

#### Get Storage Status
- **Endpoint**: `GET /api/storage/status`
- **Response**: Storage information
```json
{
    "total_bytes": 10737418240,
    "used_bytes": 8967916,
    "available_bytes": 10728450324,
    "usage_percent": 0.084
}
```

## Web Interface

The camera system includes a web-based UI that provides easy access to all camera functionality:

### Camera Feed
- Live video feed display
- FPS counter
- Motion detection indicator
- Camera selection dropdown
- Resolution settings

### Recording Controls
- Start/Stop recording buttons
- Recording duration display
- Frame counter
- Recording indicator

### Recent Recordings
- List of recorded videos
- Download and delete options
- Recording details (timestamp, duration, size)

### Camera Settings
- Resolution selection
- Settings update button

## Error Handling

The API includes comprehensive error handling:

- Invalid camera selection
- Camera initialization failures
- Recording errors
- Storage limitations
- Missing camera errors

Error responses follow this format:
```json
{
    "status": "error",
    "error": "Error message description"
}
```

## Implementation Notes

- The camera system supports multiple resolutions: 640x480, 1280x720, and 1920x1080
- Motion detection is performed in real-time
- Recordings are saved in AVI format
- The system includes automatic cleanup of failed recordings
- Status polling occurs every second to update UI elements
- All API endpoints use JSON for request/response data
- Video streaming is optimized for real-time display 
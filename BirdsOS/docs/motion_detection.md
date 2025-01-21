# Motion Detection System

## Overview
The BirdsOS motion detection system uses computer vision techniques to detect movement in the camera feed. It employs frame differencing, contour detection, and noise reduction to provide reliable motion detection capabilities.

## Technical Implementation

### Parameters
```python
motion_detected: bool      # Current motion detection status
prev_frame: np.array      # Previous frame for comparison
motion_threshold: int     # Base threshold for motion (1000)
min_motion_area: int      # Minimum area to trigger detection (500 pixels)
motion_sensitivity: int   # Threshold for pixel differences (25, range 0-255)
```

### Algorithm Steps
1. **Pre-processing**
   - Convert frame to grayscale for simpler processing
   - Apply Gaussian blur (21x21 kernel) to reduce noise
   - Store first frame as reference if none exists

2. **Frame Analysis**
   - Calculate absolute difference between current and previous frames
   - Apply binary threshold using motion_sensitivity
   - Dilate thresholded image to fill holes

3. **Motion Detection**
   - Find contours in the thresholded image
   - Filter contours by minimum area (min_motion_area)
   - Draw green rectangles around detected motion areas (debug)
   - Update previous frame for next comparison

### Visual Feedback
- Green rectangles are drawn around areas where motion is detected
- These rectangles are included in the video feed for debugging purposes

## Configuration

### Sensitivity Adjustment
- `motion_sensitivity` (default: 25)
  - Lower values: More sensitive to small changes
  - Higher values: Only detect significant changes
  - Range: 0-255

- `min_motion_area` (default: 500)
  - Lower values: Detect smaller moving objects
  - Higher values: Only detect larger movements
  - Unit: Pixels²

## Integration

### API Endpoints
Motion detection status is available through:
- `/api/camera/status` - Returns current motion status
- Camera info includes `motion_detected` boolean field

### Real-time Updates
- Motion detection runs on every frame in the camera thread
- Status updates are logged when motion is detected
- UI can poll status endpoint for updates

## Performance Considerations
- Frame processing is done in grayscale for efficiency
- Gaussian blur helps reduce false positives from noise
- Frame buffer maintains 30 FPS performance target
- Motion detection adds minimal overhead to frame processing

## Debug and Troubleshooting
- Green rectangles in video feed indicate detected motion areas
- Debug logs are generated when motion is detected
- Motion parameters can be adjusted for different environments
- Frame processing steps can be visualized for debugging 
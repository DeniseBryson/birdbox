# Manual Installation Guide

This guide provides step-by-step instructions for manually installing BirdsOS on any system. While the project is optimized for Raspberry Pi, you can run it on other systems for development or testing purposes.

## System Requirements

### Minimum Requirements
- Python 3.7 or higher
- 1GB RAM
- 1GB free disk space
- Webcam (for camera features)
- GPIO capability (for hardware control features)

### Development Mode Requirements
- Python 3.7 or higher
- 2GB RAM
- 5GB free disk space
- Any webcam (optional, mock camera available)
- No GPIO required (mock GPIO available)

## Installation Steps

### 1. Prepare the Environment

```bash
# Create and enter project directory
mkdir birdbox
cd birdbox

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

### 2. Clone the Repository

```bash
git clone https://github.com/DeniseBryson/birdbox.git .
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install system packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3-opencv \
    libatlas-base-dev \
    libgstreamer1.0-0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good

# Install Python requirements
pip install -r requirements.txt
```

For other operating systems, install equivalent packages using your system's package manager.

### 4. Create Configuration

Create a `.env` file in the project root:

```bash
# Create and edit .env file
cat > .env << EOL
# BirdsOS Environment Configuration
FLASK_APP=app.py
FLASK_ENV=development  # Change to 'production' for production setup
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
MAX_CONTENT_LENGTH=16777216

# Storage Configuration
STORAGE_PATH=./storage
MAX_STORAGE_GB=5
WARNING_THRESHOLD=0.85

# Camera Configuration
CAMERA_RESOLUTION_WIDTH=640
CAMERA_RESOLUTION_HEIGHT=480
CAMERA_FRAMERATE=30
CAMERA_FORMAT=h264
CAMERA_BUFFER_TIME=5
CAMERA_POST_TIME=10

# GPIO Configuration
ENABLE_HARDWARE=false  # Set to true only if GPIO hardware is available
GPIO_MODE=BCM

# WebSocket Configuration
WS_ENABLED=true

# Testing Configuration
TESTING=false
EOL
```

### 5. Create Required Directories

```bash
# Create storage structure
mkdir -p storage/{recordings,logs}
```

### 6. Run Tests

```bash
# Run the test suite
python -m pytest
```

### 7. Development Server

```bash
# Start the development server
python app.py
```

The application will be available at `http://localhost:5000`

## Production Deployment

For production deployment, additional steps are recommended:

### Using Systemd (Linux)

1. Create a service file:
```bash
sudo nano /etc/systemd/system/birdbox.service
```

2. Add the following content (adjust paths as needed):
```ini
[Unit]
Description=BirdsOS Web Interface
After=network.target

[Service]
User=<your-username>
WorkingDirectory=/path/to/birdbox
Environment="PATH=/path/to/birdbox/venv/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
ExecStart=/path/to/birdbox/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl enable birdbox
sudo systemctl start birdbox
```

### Using Docker

A Dockerfile is provided for containerized deployment. Build and run with:

```bash
docker build -t birdbox .
docker run -p 5000:5000 birdbox
```

## Troubleshooting

### Common Issues

1. **Camera Not Working**
   - Check if OpenCV is installed correctly
   - Verify camera permissions
   - Try running with mock camera: Set `ENABLE_HARDWARE=false` in `.env`

2. **GPIO Errors**
   - Verify GPIO library installation
   - Check hardware permissions
   - Use mock GPIO for testing: Set `ENABLE_HARDWARE=false` in `.env`

3. **Permission Issues**
   - Ensure correct file permissions on storage directories
   - Check user permissions for camera/GPIO access

### Logs

- Application logs: `storage/logs/birdbox.log`
- Error logs: `storage/logs/birdbox_error.log`

## Development Mode

For development, set these environment variables:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
```

This enables:
- Debug mode
- Auto-reload on code changes
- Detailed error pages
- Mock hardware support 
#!/bin/bash

echo "BirdsOS Setup Script"
echo "===================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi. Some features may not work on other systems."
fi

# Verify OS is Raspberry Pi OS Lite
if ! grep -q "lite" /etc/os-release; then
    echo "Warning: For optimal performance, Raspberry Pi OS Lite is recommended."
fi

# Check for SSH key
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "SSH key not found. Setting up SSH key..."
    ssh-keygen -t rsa -b 4096 -N "" -f ~/.ssh/id_rsa
    echo "Please add this SSH key to your GitHub account before continuing:"
    cat ~/.ssh/id_rsa.pub
    echo ""
    read -p "Press Enter once you've added the SSH key to GitHub..."
fi

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    python3-opencv \
    libatlas-base-dev \
    python3-rpi.gpio \
    htop \
    psutil

# Enable required interfaces
echo "Configuring Raspberry Pi interfaces..."
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_i2c 0

# Create full project structure
echo "Creating project directory structure..."
mkdir -p ~/BirdsOS/{features,routes,static,templates,tests,logs,recordings}
mkdir -p ~/BirdsOS/features/{camera,gpio}
mkdir -p ~/BirdsOS/storage/{videos,data,backups,logs}

# Clone repository
echo "Cloning BirdsOS repository (AIgen2 branch)..."
git clone -b AIgen2 git@github.com:DeniseBryson/birdbox.git .

# Create virtual environment with specific Python version
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install test dependencies first
echo "Installing test dependencies..."
pip install pytest pytest-cov pytest-flask

# Install application dependencies
echo "Installing Python requirements..."
pip install --upgrade pip
pip install opencv-python-headless
pip install -r requirements.txt

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating environment configuration..."
    cat > .env << EOL
# BirdsOS Environment Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
MAX_CONTENT_LENGTH=16777216  # 16MB as specified in app.py

# Storage Configuration
STORAGE_PATH=/home/pi/BirdsOS/storage
MAX_STORAGE_GB=5
WARNING_THRESHOLD=0.80

# Camera Configuration
CAMERA_RESOLUTION_WIDTH=640
CAMERA_RESOLUTION_HEIGHT=480
CAMERA_FRAMERATE=30
CAMERA_FORMAT=h264
CAMERA_BUFFER_TIME=5
CAMERA_POST_TIME=10

# GPIO Configuration
ENABLE_HARDWARE=true
GPIO_MODE=BCM

# WebSocket Configuration
WS_ENABLED=true

# Testing Configuration
TESTING=false
EOL
fi

# Set up systemd service
echo "Setting up systemd service..."
sudo tee /etc/systemd/system/birdsos.service << EOL
[Unit]
Description=BirdsOS Web Interface
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/BirdsOS
Environment="PATH=/home/pi/BirdsOS/venv/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
ExecStart=/home/pi/BirdsOS/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/BirdsOS/storage/logs/birdsos.log
StandardError=append:/home/pi/BirdsOS/storage/logs/birdsos_error.log

[Install]
WantedBy=multi-user.target
EOL

# Run initial tests
echo "Running initial tests..."
if ! python -m pytest; then
    echo "Tests failed! Please check the test output above."
    echo "Would you like to continue with the setup anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Setup aborted due to test failures."
        exit 1
    fi
    echo "Continuing setup despite test failures..."
fi

# Set up log rotation
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/birdsos << EOL
/home/pi/BirdsOS/storage/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOL

# Enable and start service
sudo systemctl enable birdsos
sudo systemctl start birdsos

echo "Setup complete!"
echo "===================="
echo "BirdsOS should now be running at: http://localhost:5000"
echo ""
echo "Performance Recommendations:"
echo "1. Use a Class 10 SD card (minimum 16GB)"
echo "2. Monitor system resources with 'htop'"
echo "3. Check temperatures with 'vcgencmd measure_temp'"
echo "4. View logs in storage/logs directory"
echo ""
echo "Important commands:"
echo "- Check service status: sudo systemctl status birdsos"
echo "- View logs: sudo journalctl -u birdsos"
echo "- Monitor resources: htop"
echo "- Check temperature: vcgencmd measure_temp"
echo "- Restart service: sudo systemctl restart birdsos"
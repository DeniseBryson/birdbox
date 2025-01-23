#!/bin/bash

echo "BirdsOS Setup Script"
echo "===================="

# Get current user
CURRENT_USER=$(whoami)
INSTALL_PATH="/home/${CURRENT_USER}/birdbox"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Error: This script must be run on a Raspberry Pi"
    exit 1
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
    libgstreamer1.0-0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    htop \
    psutil

# Enable required interfaces
echo "Configuring Raspberry Pi interfaces..."
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_i2c 0

# Create project directory
echo "Setting up project directory..."
mkdir -p ${INSTALL_PATH}
cd ${INSTALL_PATH}

# Clone repository
echo "Cloning BirdsOS repository (AIgen2 branch)..."
git clone -b AIgen2 git@github.com:DeniseBryson/birdbox.git .

# Create required directories
echo "Creating storage directories..."
mkdir -p storage/{recordings,logs}

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Calculating available storage space..."
    # Get total space in GB (using df, filtering root filesystem, and extracting size in KB)
    TOTAL_SPACE_GB=$(df -k / | awk 'NR==2 {printf "%.0f", $2/1024/1024}')
    # Calculate 75% of total space
    MAX_STORAGE_GB=$(($TOTAL_SPACE_GB * 75 / 100))
    
    echo "Creating environment configuration..."
    cat > .env << EOL
# BirdsOS Environment Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
MAX_CONTENT_LENGTH=16777216

# Storage Configuration
STORAGE_PATH=${INSTALL_PATH}/storage
MAX_STORAGE_GB=$MAX_STORAGE_GB  # 75% of available SD card space (${TOTAL_SPACE_GB}GB total)
WARNING_THRESHOLD=0.85

# Camera Configuration
CAMERA_RESOLUTION_WIDTH=640
CAMERA_RESOLUTION_HEIGHT=480
CAMERA_FRAMERATE=20
CAMERA_FORMAT=h264
CAMERA_BUFFER_TIME=5
CAMERA_POST_TIME=10

# GPIO Configuration
ENABLE_HARDWARE=true
GPIO_MODE=BCM

# WebSocket Configuration
WS_ENABLED=true

# Testing Configuration
TESTING=true  # Set to true during setup
EOL

    echo "Storage space calculation:"
    echo "Total SD card space: ${TOTAL_SPACE_GB}GB"
    echo "Allocated for BirdsOS: ${MAX_STORAGE_GB}GB (75%)"
fi

# Create config verification script
echo "Creating configuration verification script..."
cat > verify_config.py << EOL
import os
from dotenv import load_dotenv

def verify_config():
    load_dotenv()
    required_vars = [
        'FLASK_APP',
        'STORAGE_PATH',
        'MAX_STORAGE_GB',
        'CAMERA_RESOLUTION_WIDTH',
        'CAMERA_RESOLUTION_HEIGHT',
        'CAMERA_FRAMERATE',
        'GPIO_MODE'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("Error: Missing required environment variables:", ", ".join(missing))
        return False
        
    # Verify storage path exists
    storage_path = os.getenv('STORAGE_PATH')
    if not os.path.exists(storage_path):
        print(f"Error: Storage path {storage_path} does not exist")
        return False
        
    return True

if __name__ == '__main__':
    if not verify_config():
        exit(1)
EOL

# Verify configuration
echo "Verifying configuration..."
if ! python verify_config.py; then
    echo "Error: Configuration verification failed!"
    exit 1
fi

# Export environment variables for testing
echo "Loading environment for tests..."
set -a  # automatically export all variables
source .env
set +a

# Run tests before proceeding with service setup
echo "Running tests to verify installation..."
if ! python -m pytest; then
    echo "Error: Tests failed!"
    echo "Would you like to:"
    echo "1. Exit setup (recommended)"
    echo "2. Continue anyway (not recommended)"
    read -p "Enter your choice (1/2): " choice
    case $choice in
        1)
            echo "Setup aborted. Please fix the test failures and try again."
            exit 1
            ;;
        2)
            echo "Warning: Continuing setup despite test failures. The system may not work correctly."
            ;;
        *)
            echo "Invalid choice. Aborting setup."
            exit 1
            ;;
    esac
fi

# Set up systemd service
echo "Setting up systemd service..."
sudo tee /etc/systemd/system/birdbox.service << EOL
[Unit]
Description=BirdsOS Web Interface
After=network.target

[Service]
User=${CURRENT_USER}
WorkingDirectory=${INSTALL_PATH}
Environment="PATH=${INSTALL_PATH}/venv/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
ExecStart=${INSTALL_PATH}/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=append:${INSTALL_PATH}/storage/logs/birdbox.log
StandardError=append:${INSTALL_PATH}/storage/logs/birdbox_error.log

[Install]
WantedBy=multi-user.target
EOL

# Set up log rotation
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/birdbox << EOL
${INSTALL_PATH}/storage/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ${CURRENT_USER} ${CURRENT_USER}
}
EOL

# Enable and start service
sudo systemctl enable birdbox
sudo systemctl start birdbox

echo "Setup complete!"
echo "===================="
echo "BirdsOS is now running at: http://localhost:5000"
echo ""
echo "Performance Recommendations for Raspberry Pi 3B:"
echo "1. Use a high-quality Class 10 SD card (32GB recommended)"
echo "2. Monitor CPU temperature regularly - should stay under 80°C"
echo "3. Consider adding a cooling fan if running 24/7"
echo "4. Check storage usage regularly with 'df -h'"
echo ""
echo "Important commands:"
echo "- Check service status: sudo systemctl status birdbox"
echo "- View logs: tail -f ${INSTALL_PATH}/storage/logs/birdbox.log"
echo "- Monitor resources: htop"
echo "- Check temperature: vcgencmd measure_temp"
echo "- Restart service: sudo systemctl restart birdbox"
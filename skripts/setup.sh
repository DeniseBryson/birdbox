#!/bin/bash
set -e

# Basic variables
INSTALL_PATH="/home/birds/birdbox"
LOG_DIR="/var/log/birdbox"

echo "BirdsOS Setup Script"
echo "===================="
echo "Installing to: ${INSTALL_PATH}"

# Update system and install packages
echo "Installing system packages..."
sudo apt-get update
sudo apt-get install -y \
    git \
    python3-pip \
    python3-venv \
    python3-opencv \
    python3-rpi.gpio \
    python3-pytest \
    python3-flask \
    python3-requests \
    python3-numpy \
    python3-pillow \
    python3-dotenv

# Create project directory
echo "Setting up project directory..."
mkdir -p ${INSTALL_PATH}
cd ${INSTALL_PATH}

# Clone repository
echo "Cloning repository..."
git clone --depth 1 -b AIgen3 https://github.com/DeniseBryson/birdbox.git .  # Note the dot at the end

# Set up Python environment
echo "Setting up Python environment..."
python3 -m venv venv --system-site-packages  # This allows access to system packages
source venv/bin/activate
pip install --upgrade pip wheel

# Install Python packages that aren't available through apt
echo "Installing additional Python packages..."
pip install flask-sock  # No apt package available for this
pip install gunicorn   # Using pip for latest version
pip remove RPi.GPIO   # Ensure GPIO is available in virtual environment
pip install rpi-lgpio
pip install pytest pytest-asyncio

# Set up logging directory
echo "Setting up logging..."
sudo mkdir -p ${LOG_DIR}
sudo chown birds:birds ${LOG_DIR}

# Create service file
echo "Setting up service..."
sudo tee /etc/systemd/system/birdbox.service << EOL
[Unit]
Description=BirdsOS Web Application
After=network.target

[Service]
User=birds
Group=birds
WorkingDirectory=${INSTALL_PATH}
Environment="PATH=${INSTALL_PATH}/venv/bin"
Environment="VIRTUAL_ENV=${INSTALL_PATH}/venv"
Environment="PYTHONPATH=${INSTALL_PATH}"
ExecStart=${INSTALL_PATH}/venv/bin/python -m gunicorn \
    -w 4 \
    -b 0.0.0.0:8080 \
    --error-logfile ${LOG_DIR}/gunicorn-error.log \
    --access-logfile ${LOG_DIR}/gunicorn-access.log \
    --capture-output \
    --enable-stdio-inheritance \
    --chdir ${INSTALL_PATH} \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Start service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable birdbox
sudo systemctl restart birdbox

echo "Setup complete!"
echo "Access the web interface at: http://$(hostname -I | cut -d' ' -f1):8080"

#TODO: RUN TESTS BUT ASK USER IF THEY WANT TO RUN THEM SINCE IT WILL CHANGE PIN STATES
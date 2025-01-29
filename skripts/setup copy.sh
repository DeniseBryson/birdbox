#!/bin/bash

# Enable error handling
set -e

# Set up logging
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="/var/log/birdbox"
SETUP_LOG="${LOG_DIR}/setup_${TIMESTAMP}.log"
mkdir -p "${LOG_DIR}"

# Get current user and real user
CURRENT_USER=$(whoami)
REAL_USER=${SUDO_USER:-$USER}
INSTALL_PATH="/home/${REAL_USER}/birdbox"

# Set proper ownership of log directory
sudo chown -R ${REAL_USER}:${REAL_USER} "${LOG_DIR}"
exec 1> >(tee -a "${SETUP_LOG}") 2>&1

# Error handling function
handle_error() {
    local line_no=$1
    echo "Error occurred in setup script at line ${line_no}"
    exit 1
}

trap 'handle_error ${LINENO}' ERR

echo "BirdsOS Setup Script"
echo "===================="
echo "Setup started at: $(date)"
echo "Log file: ${SETUP_LOG}"
echo "Installing as user: ${REAL_USER}"
echo "Installation path: ${INSTALL_PATH}"
echo ""

# System requirements check
echo "Checking system requirements..."
MIN_DISK_SPACE=1000000  # 1GB in KB
MIN_MEMORY=512000       # 512MB in KB

# Check disk space
AVAILABLE_DISK=$(df -k /home | awk 'NR==2 {print $4}')
if [ "$AVAILABLE_DISK" -lt "$MIN_DISK_SPACE" ]; then
    echo "Error: Insufficient disk space. Required: 1GB, Available: $(($AVAILABLE_DISK/1024))MB"
    exit 1
fi

# Check memory
AVAILABLE_MEMORY=$(free -k | awk '/^Mem:/ {print $2}')
if [ "$AVAILABLE_MEMORY" -lt "$MIN_MEMORY" ]; then
    echo "Error: Insufficient memory. Required: 512MB, Available: $(($AVAILABLE_MEMORY/1024))MB"
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Error: This script must be run on a Raspberry Pi"
    exit 1
fi

# Configure port and SSL settings
PORT=8080
USE_HTTPS=false
CERT_DIR="/etc/birdbox/certs"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port=*)
            PORT="${1#*=}"
            shift
            ;;
        --use-https)
            USE_HTTPS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to clean up previous installation
cleanup_installation() {
    echo "Cleaning up previous installation..."
    echo "Performing full cleanup automatically..."
    rm -rf "${INSTALL_PATH}"
    rm -f ~/.ssh/birdbox_deploy_key*
    rm -f ~/.ssh/config
    sudo systemctl stop birdbox 2>/dev/null || true
    sudo systemctl disable birdbox 2>/dev/null || true
    sudo rm -f /etc/systemd/system/birdbox.service
    sudo systemctl daemon-reload
}

# Set up detailed logging
setup_logging() {
    local log_dir="/var/log/birdbox"
    sudo mkdir -p "$log_dir"
    sudo chown ${REAL_USER}:${REAL_USER} "$log_dir"
    
    # Rotate old logs
    if [ -f "$log_dir/setup.log" ]; then
        mv "$log_dir/setup.log" "$log_dir/setup.log.old"
    fi
    
    # Link current log to central location
    ln -sf "${SETUP_LOG}" "$log_dir/setup.log"
    
    # Set up log format
    exec 2> >(while read line; do echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $line" | tee -a "$SETUP_LOG"; done)
    set -E
    trap 'echo "Error occurred in setup script at line $LINENO" | tee -a "$SETUP_LOG"' ERR
}

# Set up HTTPS if requested
setup_https() {
    if [ "$USE_HTTPS" = true ]; then
        echo "Setting up HTTPS..."
        sudo mkdir -p "$CERT_DIR"
        
        # Generate self-signed certificate
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$CERT_DIR/birdbox.key" \
            -out "$CERT_DIR/birdbox.crt" \
            -subj "/CN=${HOSTNAME}"
        
        sudo chmod 600 "$CERT_DIR/birdbox.key"
        sudo chmod 644 "$CERT_DIR/birdbox.crt"
        
        # Update service configuration to use HTTPS
        GUNICORN_OPTS="--certfile=$CERT_DIR/birdbox.crt --keyfile=$CERT_DIR/birdbox.key"
        PROTOCOL="https"
    else
        GUNICORN_OPTS=""
        PROTOCOL="http"
    fi
}

# Function to test GitHub access
test_github_access() {
    local access_type=$1
    echo "Testing ${access_type} access to repository..."
    
    case $access_type in
        "HTTPS")
            if git ls-remote https://github.com/DeniseBryson/birdbox.git HEAD &>/dev/null; then
                echo "✓ Repository is accessible via HTTPS"
                return 0
            fi
            ;;
        "SSH")
            if git ls-remote git@github.com:DeniseBryson/birdbox.git HEAD &>/dev/null; then
                echo "✓ Repository is accessible via existing SSH configuration"
                return 0
            fi
            ;;
        "DEPLOY_KEY")
            if [ -f ~/.ssh/birdbox_deploy_key ] && git ls-remote git@github.com-birdbox:DeniseBryson/birdbox.git HEAD &>/dev/null; then
                echo "✓ Repository is accessible via existing deploy key"
                return 0
            fi
            ;;
    esac
    return 1
}

# Function to clone repository with retry
clone_with_retry() {
    local branch=$1
    local url=$2
    echo "Attempting to clone branch: $branch"
    rm -rf * .[!.]* ..?*  # Clear directory (including hidden files)
    
    # Try different clone methods
    if git clone --depth 1 -b $branch $url .; then
        echo "Successfully cloned using shallow clone"
        git fetch --unshallow  # Get full history
        return 0
    elif git clone --recursive -b $branch $url .; then
        echo "Successfully cloned using recursive clone"
        return 0
    else
        return 1
    fi
}

# Configure Git for large repositories
echo "Configuring Git for large repositories..."
git config --global http.postBuffer 524288000
git config --global core.compression 9
git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 60

# Try different access methods
echo "Checking repository access..."
if test_github_access "HTTPS"; then
    USE_SSH=false
elif test_github_access "SSH"; then
    USE_SSH=true
elif test_github_access "DEPLOY_KEY"; then
    USE_SSH=true
    echo "Using existing deploy key configuration"
else
    echo "Repository requires new authentication setup..."
    USE_SSH=true

    # Check for existing deploy key
    if [ -f ~/.ssh/birdbox_deploy_key ]; then
        echo "Found existing deploy key. Would you like to:"
        echo "1. Use existing key (recommended if it was working before)"
        echo "2. Generate new key (choose if old key is invalid)"
        read -p "Enter choice (1/2): " key_choice
        
        case $key_choice in
            1)
                echo "Using existing deploy key..."
                ;;
            2)
                echo "Generating new deploy key..."
                rm -f ~/.ssh/birdbox_deploy_key*
                ssh-keygen -t ed25519 -f ~/.ssh/birdbox_deploy_key -N "" -C "birdbox-deploy-key"
                ;;
            *)
                echo "Invalid choice. Using existing key..."
                ;;
        esac
    else
        echo "Generating new deploy key..."
        ssh-keygen -t ed25519 -f ~/.ssh/birdbox_deploy_key -N "" -C "birdbox-deploy-key"
    fi

    echo ""
    echo "======================== IMPORTANT SSH SETUP ========================"
    echo "Please add the following public key to your GitHub repository as a deploy key:"
    echo ""
    cat ~/.ssh/birdbox_deploy_key.pub
    echo ""
    echo "Instructions:"
    echo "1. Go to your GitHub repository settings"
    echo "2. Navigate to 'Deploy Keys'"
    echo "3. Click 'Add deploy key'"
    echo "4. Paste the above public key"
    echo "5. Give it a title like 'BirdsBox Deploy Key'"
    echo "6. Check 'Allow write access' ONLY if necessary"
    echo ""
    echo "WARNING: Do NOT use your normal GitHub SSH keys for this setup!"
    echo "This is a dedicated deploy key for security purposes."
    echo "================================================================="
    echo ""

    # Keep trying until the key works
    while true; do
        read -p "Press Enter once you've added the deploy key to GitHub..."
        
        # Configure SSH for deploy key
        echo "Configuring SSH for deploy key..."
        mkdir -p ~/.ssh
        cat > ~/.ssh/config << EOL
Host github.com-birdbox
    Hostname github.com
    IdentityFile ~/.ssh/birdbox_deploy_key
    StrictHostKeyChecking accept-new
EOL
        chmod 600 ~/.ssh/config

        # Add GitHub's SSH host key
        echo "Adding GitHub's SSH host key..."
        ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts

        # Test the connection
        if ssh -T git@github.com-birdbox 2>&1 | grep -q "successfully authenticated"; then
            echo "SSH key setup successful!"
            break
        else
            echo "SSH key verification failed. Please check the deploy key on GitHub and try again."
            echo "Make sure you've:"
            echo "1. Added the key exactly as shown above"
            echo "2. Confirmed the addition on GitHub"
            echo "3. Given appropriate permissions"
        fi
    done
fi

# Create project directory
echo "Setting up project directory..."
mkdir -p ${INSTALL_PATH}
cd ${INSTALL_PATH}

# Clone repository with retry mechanism
echo "Cloning BirdsOS repository (trying AIgen2 branch)..."
MAX_RETRIES=3
RETRY_COUNT=0

if [ -d ".git" ]; then
    echo "Git repository already exists, fetching latest changes..."
    git fetch
    if [ "$USE_SSH" = true ]; then
        git remote set-url origin git@github.com-birdbox:DeniseBryson/birdbox.git
    else
        git remote set-url origin https://github.com/DeniseBryson/birdbox.git
    fi
    # Try AIgen2 first, then fall back to main/master
    if git rev-parse --verify origin/AIgen2 >/dev/null 2>&1; then
        echo "Using AIgen2 branch..."
        git reset --hard origin/AIgen2
    elif git rev-parse --verify origin/main >/dev/null 2>&1; then
        echo "AIgen2 branch not found, falling back to main branch..."
        git reset --hard origin/main
    else
        echo "AIgen2 and main branches not found, falling back to master branch..."
        git reset --hard origin/master
    fi
else
    if [ "$USE_SSH" = true ]; then
        REPO_URL="git@github.com-birdbox:DeniseBryson/birdbox.git"
    else
        REPO_URL="https://github.com/DeniseBryson/birdbox.git"
    fi

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if git ls-remote --heads $REPO_URL AIgen2 | grep -q AIgen2; then
            if clone_with_retry "AIgen2" "$REPO_URL"; then
                break
            fi
        elif git ls-remote --heads $REPO_URL main | grep -q main; then
            if clone_with_retry "main" "$REPO_URL"; then
                break
            fi
        else
            if clone_with_retry "master" "$REPO_URL"; then
                break
            fi
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "Clone failed, retrying in 5 seconds... (Attempt $((RETRY_COUNT + 1)) of $MAX_RETRIES)"
            sleep 5
        fi
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Error: Failed to clone repository after $MAX_RETRIES attempts"
        echo "Please check your internet connection and try again"
        exit 1
    fi
fi

# Create and set up Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv ${INSTALL_PATH}/venv
source ${INSTALL_PATH}/venv/bin/activate || {
    echo "Error: Failed to activate virtual environment"
    exit 1
}

# Upgrade pip and install wheel
echo "Upgrading pip and installing wheel..."
python3 -m pip install --upgrade pip wheel || {
    echo "Error: Failed to upgrade pip and install wheel"
    exit 1
}

# Install Python dependencies
echo "Installing Python dependencies..."
if [ -f "${INSTALL_PATH}/requirements.txt" ]; then
    pip install -r "${INSTALL_PATH}/requirements.txt" || {
        echo "Error: Failed to install requirements"
        exit 1
    }
    echo "✓ Successfully installed Python dependencies"
else
    echo "Error: requirements.txt not found in ${INSTALL_PATH}"
    exit 1
fi

# Install additional packages
echo "Installing additional packages..."
pip install gunicorn || {
    echo "Error: Failed to install gunicorn"
    exit 1
}
echo "✓ Successfully installed additional packages"

# Verify installations
echo "Verifying package installations..."
python3 -c "import flask; import gunicorn; import cv2; import numpy; from PIL import Image" || {
    echo "Error: Package verification failed"
    exit 1
}
echo "✓ Package verification successful"

# Debug logging
echo "DEBUG: Starting service setup..."

# Initialize logging
setup_logging

# Setup systemd service for production server
echo "Setting up production server service..."
sudo mkdir -p "${LOG_DIR}" || {
    echo "Error: Failed to create log directory"
    exit 1
}
sudo chown ${REAL_USER}:${REAL_USER} "${LOG_DIR}" || {
    echo "Error: Failed to set log directory permissions"
    exit 1
}

# Create and configure systemd service
echo "Setting up systemd service..."
SERVICE_FILE="/etc/systemd/system/birdbox.service"
echo "DEBUG: Creating service file at ${SERVICE_FILE}"

cat > "${SERVICE_FILE}.tmp" << EOL || {
    echo "Error: Failed to create temporary service file"
    exit 1
}
[Unit]
Description=BirdsOS Web Application
After=network.target

[Service]
User=${REAL_USER}
Group=${REAL_USER}
WorkingDirectory=${INSTALL_PATH}
Environment="PATH=${INSTALL_PATH}/venv/bin"
Environment="VIRTUAL_ENV=${INSTALL_PATH}/venv"
Environment="PYTHONPATH=${INSTALL_PATH}"
ExecStart=${INSTALL_PATH}/venv/bin/python -m gunicorn -w 4 -b 0.0.0.0:8080 --error-logfile ${LOG_DIR}/gunicorn-error.log --access-logfile ${LOG_DIR}/gunicorn-access.log app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

echo "DEBUG: Moving service file to final location..."
# Move the temporary file to the final location
sudo mv "${SERVICE_FILE}.tmp" "${SERVICE_FILE}" || {
    echo "Error: Failed to move service file"
    exit 1
}
sudo chmod 644 "${SERVICE_FILE}" || {
    echo "Error: Failed to set service file permissions"
    exit 1
}

echo "DEBUG: Reloading systemd..."
# Enable and start the service
echo "Enabling and starting BirdsOS service..."
sudo systemctl daemon-reload || {
    echo "Failed to reload systemd configuration"
    exit 1
}

sudo systemctl enable birdbox || {
    echo "Failed to enable birdbox service"
    exit 1
}

sudo systemctl restart birdbox || {
    echo "Failed to start birdbox service"
    echo "Checking service logs..."
    sudo journalctl -u birdbox -n 50 --no-pager
    exit 1
}

# Check service status
echo "Checking service status..."
if sudo systemctl is-active --quiet birdbox; then
    echo "✓ BirdsOS service is running"
else
    echo "⚠️  BirdsOS service failed to start. Check logs:"
    echo "- Setup log: ${SETUP_LOG}"
    echo "- Service logs: journalctl -u birdbox"
    echo "- Application logs: ${LOG_DIR}/gunicorn-*.log"
    exit 1
fi

# Test camera with rpicam-still
echo "Testing camera functionality..."
if rpicam-still -t 2000 -o ~/test_image.jpg 2>/dev/null; then
    echo "✓ Camera test successful - saved as ~/test_image.jpg"
    echo "Camera resolution: $(identify -format '%wx%h' ~/test_image.jpg 2>/dev/null || echo 'unknown')"
else
    echo "⚠️  Camera test failed. This might be normal if no camera is connected."
    echo "If a camera is connected, please check:"
    echo "1. Camera ribbon cable connection"
    echo "2. Camera module compatibility"
    echo "3. Camera interface enablement in raspi-config"
fi

# Verify camera setup
echo "Verifying camera setup..."
if ! vcgencmd get_camera | grep -q "supported=1 detected=1"; then
    echo "WARNING: Camera is not properly detected!"
    echo "Please check:"
    echo "1. Camera ribbon cable is properly connected"
    echo "2. Camera is enabled in raspi-config"
    echo "3. Camera module is not damaged"
fi

# Check camera permissions
echo "Setting up camera permissions..."
if [ -e "/dev/video0" ]; then
    echo "Camera device found at /dev/video0"
    sudo usermod -a -G video ${REAL_USER}
    sudo chmod 660 /dev/video0
else
    echo "WARNING: Camera device not found at /dev/video0"
    echo "Try rebooting after setup completes"
fi

echo "Setup complete!"
echo "===================="
echo "Setup log saved to: ${SETUP_LOG}"
echo ""
echo "Next steps:"
echo "1. Check the camera setup results above"
echo "2. If needed, run 'sudo reboot' to apply all changes"
echo "3. Access the web interface at ${PROTOCOL}://${HOSTNAME}:8080"
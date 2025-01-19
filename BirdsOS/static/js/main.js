// BirdsOS Main JavaScript

// Update status information every 5 seconds
setInterval(updateStatus, 5000);

// Motor control event listeners
document.getElementById('startMotor').addEventListener('click', startMotor);
document.getElementById('stopMotor').addEventListener('click', stopMotor);
document.getElementById('emergencyStop').addEventListener('click', emergencyStop);

// Status update function
async function updateStatus() {
    try {
        const response = await fetch('/status');
        const data = await response.json();

        // Update system status
        document.getElementById('systemStatus').textContent = data.status;

        // Update storage status if available
        if (data.storage) {
            const storage = data.storage;
            const usedPercent = ((storage.used / storage.total) * 100).toFixed(1);
            document.getElementById('storageStatus').textContent =
                `${usedPercent}% used (${formatBytes(storage.free)} free)`;
        }

        // Update food level if available
        if (data.food_level) {
            document.getElementById('foodLevel').textContent =
                `${data.food_level.percent}% remaining`;
        }
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Motor control functions
async function startMotor() {
    try {
        const response = await fetch('/api/motor/start', {
            method: 'POST'
        });
        const data = await response.json();
        if (data.status === 'success') {
            showNotification('Motors started successfully');
        } else {
            showNotification('Error starting motors', 'error');
        }
    } catch (error) {
        showNotification('Error starting motors', 'error');
    }
}

async function stopMotor() {
    try {
        const response = await fetch('/api/motor/stop', {
            method: 'POST'
        });
        const data = await response.json();
        if (data.status === 'success') {
            showNotification('Motors stopped successfully');
        } else {
            showNotification('Error stopping motors', 'error');
        }
    } catch (error) {
        showNotification('Error stopping motors', 'error');
    }
}

async function emergencyStop() {
    if (confirm('Are you sure you want to activate EMERGENCY STOP?')) {
        try {
            const response = await fetch('/api/motor/emergency-stop', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.status === 'success') {
                showNotification('EMERGENCY STOP activated!', 'warning');
            } else {
                showNotification('Error during emergency stop', 'error');
            }
        } catch (error) {
            showNotification('Error during emergency stop', 'error');
        }
    }
}

// Utility functions
function formatBytes(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
}

function showNotification(message, type = 'success') {
    // TODO: Implement notification system
    console.log(`${type}: ${message}`);
}

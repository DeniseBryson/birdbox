/**
 * Storage configuration management
 * Handles loading and saving storage settings
 */

// Storage Configuration Module

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

async function loadStorageConfig() {
    try {
        const response = await fetch('/api/v1/config/storage');
        const data = await response.json();
        
        // Convert bytes to appropriate unit
        const limitInGB = data.storage_limit / (1024 * 1024 * 1024);
        document.getElementById('storage-limit').value = limitInGB.toFixed(1);
        document.getElementById('storage-unit').value = 'GB';
        
        document.getElementById('warning-threshold').value = 
            (data.warning_threshold * 100).toFixed(0);
        document.getElementById('retention-days').value = data.retention_days;
        
        // Update disk information
        const usedPercent = (data.disk_used / data.disk_total * 100).toFixed(1);
        const diskUsageEl = document.getElementById('disk-usage');
        diskUsageEl.style.width = usedPercent + '%';
        diskUsageEl.textContent = usedPercent + '%';
        
        // Set progress bar color based on usage
        if (usedPercent > 90) {
            diskUsageEl.classList.add('bg-danger');
        } else if (usedPercent > 75) {
            diskUsageEl.classList.add('bg-warning');
        }
        
        document.getElementById('disk-info').textContent = 
            `Total: ${formatBytes(data.disk_total)} | Free: ${formatBytes(data.disk_free)}`;
    } catch (error) {
        console.error('Error loading storage config:', error);
        alert('Failed to load storage configuration');
    }
}

async function saveStorageConfig(event) {
    event.preventDefault();
    
    try {
        // Convert input to bytes
        const unit = document.getElementById('storage-unit').value;
        const limit = parseFloat(document.getElementById('storage-limit').value);
        const limitInBytes = unit === 'GB' ? 
            limit * 1024 * 1024 * 1024 : 
            limit * 1024 * 1024;
        
        const config = {
            storage_limit: limitInBytes,
            warning_threshold: parseFloat(document.getElementById('warning-threshold').value) / 100,
            retention_days: parseInt(document.getElementById('retention-days').value)
        };
        
        const response = await fetch('/api/v1/config/storage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            alert('Storage configuration updated successfully');
            await loadStorageConfig();  // Reload to show new values
        } else {
            alert('Failed to update storage configuration: ' + data.message);
        }
    } catch (error) {
        console.error('Error saving storage config:', error);
        alert('Failed to save storage configuration');
    }
}

// Initialize the storage configuration UI
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('storage-config-form');
    if (form) {
        form.addEventListener('submit', saveStorageConfig);
        loadStorageConfig();
    }
}); 
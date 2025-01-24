/**
 * Version Manager Module
 * Handles version checking and system updates
 */

async function getCurrentVersion() {
    try {
        const response = await fetch('/api/v1/system/version');
        const data = await response.json();
        
        document.getElementById('commit-hash').textContent = data.commit_hash.substring(0, 7);
        document.getElementById('commit-date').textContent = 
            new Date(data.commit_date).toLocaleDateString();
    } catch (error) {
        console.error('Error getting version:', error);
        document.getElementById('commit-hash').textContent = 'Error';
    }
}

async function checkForUpdates() {
    try {
        const button = document.getElementById('check-update');
        const statusElement = document.getElementById('update-status');
        const updateInfo = document.getElementById('update-info');
        const applyButton = document.getElementById('apply-update');
        
        button.disabled = true;
        statusElement.textContent = 'Checking for updates...';
        
        const response = await fetch('/api/v1/system/check-update');
        const data = await response.json();
        
        if (data.update_available) {
            statusElement.textContent = 'Update available!';
            updateInfo.classList.remove('d-none');
            applyButton.classList.remove('d-none');
            
            // Show changelog
            const changes = data.changes.map(c => `- ${c}`).join('\n');
            document.getElementById('update-changes').textContent = changes;
        } else {
            statusElement.textContent = 'System is up to date';
            updateInfo.classList.add('d-none');
            applyButton.classList.add('d-none');
        }
    } catch (error) {
        console.error('Error checking for updates:', error);
        statusElement.textContent = 'Error checking for updates';
    } finally {
        document.getElementById('check-update').disabled = false;
    }
}

async function applyUpdate() {
    if (!confirm('Are you sure you want to update the system? The service will restart.')) {
        return;
    }
    
    try {
        const button = document.getElementById('apply-update');
        const statusElement = document.getElementById('update-status');
        
        button.disabled = true;
        statusElement.textContent = 'Applying update...';
        
        const response = await fetch('/api/v1/system/update', {
            method: 'POST'
        });
        
        if (response.ok) {
            statusElement.textContent = 'Update successful! Restarting...';
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } else {
            const data = await response.json();
            throw new Error(data.message || 'Update failed');
        }
    } catch (error) {
        console.error('Error applying update:', error);
        document.getElementById('update-status').textContent = 
            'Error applying update: ' + error.message;
        document.getElementById('apply-update').disabled = false;
    }
}

// Initialize version info
document.addEventListener('DOMContentLoaded', () => {
    getCurrentVersion();
    
    const checkButton = document.getElementById('check-update');
    const applyButton = document.getElementById('apply-update');
    
    if (checkButton) {
        checkButton.addEventListener('click', checkForUpdates);
    }
    
    if (applyButton) {
        applyButton.addEventListener('click', applyUpdate);
    }
}); 
/**
 * Storage status management for BirdsOS dashboard
 */

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function updateStorageStatus() {
    fetch('/api/v1/maintenance/storage/status')
        .then(response => response.json())
        .then(data => {
            const stats = data.storage;
            
            // Update progress bar
            const usagePercent = (stats.storage_status.used / stats.storage_status.total * 100).toFixed(1);
            const progressBar = document.getElementById('storage-progress');
            progressBar.style.width = usagePercent + '%';
            progressBar.textContent = usagePercent + '%';
            
            // Update colors based on warning status
            if (stats.storage_status.warning) {
                progressBar.classList.remove('bg-success', 'bg-info');
                progressBar.classList.add('bg-warning');
                document.getElementById('storage-warning').classList.remove('d-none');
            } else {
                progressBar.classList.remove('bg-warning');
                progressBar.classList.add('bg-success');
                document.getElementById('storage-warning').classList.add('d-none');
            }
            
            // Update storage details
            const details = `Used: ${formatBytes(stats.storage_status.used)} of ${formatBytes(stats.storage_status.total)}`;
            document.getElementById('storage-details').textContent = details;
            
            // Update video statistics
            const videoStats = `Total Videos: ${stats.total_videos} (${formatBytes(stats.total_size)})`;
            document.getElementById('video-stats').textContent = videoStats;
            
            // Update video list if available
            if (stats.video_files && stats.video_files.length > 0) {
                const videoList = stats.video_files.slice(0, 5).map(video => `
                    <div class="mb-1">
                        <strong>${video.name}</strong><br>
                        <small class="text-muted">
                            Size: ${formatBytes(video.size)} | 
                            Modified: ${formatDate(video.modified)}
                        </small>
                    </div>
                `).join('');
                document.getElementById('video-list').innerHTML = videoList;
            } else {
                document.getElementById('video-list').innerHTML = 'No videos found';
            }
        })
        .catch(error => {
            console.error('Error fetching storage status:', error);
            document.getElementById('storage-details').textContent = 'Error loading storage status';
        });
}

// Initialize storage status updates when the document is loaded
document.addEventListener('DOMContentLoaded', () => {
    updateStorageStatus();
    setInterval(updateStorageStatus, 30000); // Update every 30 seconds
}); 
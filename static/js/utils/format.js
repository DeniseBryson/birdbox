/**
 * Utility functions for formatting values
 */

/**
 * Format bytes into human readable string
 * @param {number} bytes - Number of bytes to format
 * @param {number} decimals - Number of decimal places to show
 * @returns {string} Formatted string (e.g., "1.5 GB")
 */
export function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format date to locale string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
export function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
} 
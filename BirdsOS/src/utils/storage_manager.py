"""
Storage management utilities for BirdsOS
"""
import os
import shutil
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path
import cv2

logger = logging.getLogger('BirdsOS')

class StorageManager:
    def __init__(self, base_path: str, storage_limit_gb: float = 10.0, warning_threshold: float = 0.85):
        """
        Initialize storage manager
        
        Args:
            base_path: Base directory for storing recordings and data
            storage_limit_gb: Maximum storage limit in gigabytes
            warning_threshold: Threshold (0-1) at which to start warning about storage
        """
        self.base_path = Path(base_path)
        self.storage_limit = storage_limit_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.warning_threshold = warning_threshold
        self.recordings_path = self.base_path  # Changed: Use base_path directly for recordings
        self.data_path = self.base_path / 'data'
        
        # Create necessary directories
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized StorageManager with {storage_limit_gb}GB limit at {self.recordings_path}")
        
        # Clean up any failed recordings on startup
        self.cleanup_failed_recordings()
        
    def get_storage_status(self) -> Dict[str, float]:
        """
        Get current storage status
        
        Returns:
            Dict containing total, used, and available storage in bytes,
            and usage percentage
        """
        try:
            # Get disk usage for the recordings directory
            if not self.recordings_path.exists():
                self.recordings_path.mkdir(parents=True)
                
            total, used, free = shutil.disk_usage(self.recordings_path)
            
            # Calculate usage relative to our storage limit
            used_in_recordings = sum(f.stat().st_size for f in self.recordings_path.glob('*.*') if f.is_file())
            
            return {
                'total_bytes': self.storage_limit,  # Use our configured limit
                'used_bytes': used_in_recordings,  # Only count our recordings
                'available_bytes': self.storage_limit - used_in_recordings,
                'usage_percent': (used_in_recordings / self.storage_limit) * 100 if self.storage_limit > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting storage status: {str(e)}")
            return {
                'total_bytes': self.storage_limit,
                'used_bytes': 0,
                'available_bytes': self.storage_limit,
                'usage_percent': 0
            }
        
    def check_storage_warning(self) -> Tuple[bool, str]:
        """
        Check if storage usage exceeds warning threshold
        
        Returns:
            Tuple of (warning_active, warning_message)
        """
        status = self.get_storage_status()
        usage_percent = status['usage_percent']
        
        if usage_percent >= (self.warning_threshold * 100):
            msg = f"Storage warning: {usage_percent:.1f}% used (threshold: {self.warning_threshold * 100}%)"
            logger.warning(msg)
            return True, msg
        return False, ""
        
    def cleanup_old_recordings(self, days_to_keep: int = 30) -> int:
        """
        Remove recordings older than specified days
        
        Args:
            days_to_keep: Number of days to keep recordings for
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for file_path in self.recordings_path.glob('*.mp4'):
            if file_path.stat().st_mtime < cutoff_date:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Deleted old recording: {file_path.name}")
                
        return deleted_count
        
    def ensure_storage_available(self, required_bytes: int) -> bool:
        """
        Check if there is enough storage available
        
        Args:
            required_bytes: Number of bytes needed
            
        Returns:
            True if storage is available, False otherwise
        """
        try:
            status = self.get_storage_status()
            
            # Check if adding required_bytes would exceed storage limit
            if status['used_bytes'] + required_bytes > self.storage_limit:
                logger.warning(f"Storage limit would be exceeded. Need {required_bytes} bytes, "
                             f"but only {self.storage_limit - status['used_bytes']} available "
                             f"before hitting limit of {self.storage_limit} bytes")
                return False
                
            # Also check actual available disk space
            if required_bytes > status['available_bytes']:
                logger.warning(f"Not enough disk space. Need {required_bytes} bytes, "
                             f"but only {status['available_bytes']} available")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error checking storage availability: {str(e)}")
            return False
        
    def save_recording(self, frames: list, timestamp: Optional[datetime] = None) -> Optional[Path]:
        """
        Save recording frames to file
        
        Args:
            frames: List of frames to save
            timestamp: Optional timestamp for the recording
            
        Returns:
            Path to saved file or None if save failed
        """
        if not frames:
            return None
            
        timestamp = timestamp or datetime.now()
        filename = timestamp.strftime("%Y%m%d_%H%M%S.avi")  # Using .avi for MJPG
        filepath = self.recordings_path / filename
        
        # Get frame dimensions from first frame
        height, width = frames[0].shape[:2]
        
        # Estimate size based on frame dimensions and compression
        # MJPG typically compresses to about 1/5th of raw size for simple frames
        # We use a conservative estimate here
        bytes_per_pixel = 3  # BGR format
        raw_frame_size = width * height * bytes_per_pixel
        compressed_frame_size = raw_frame_size // 5  # Conservative compression estimate
        
        # Add overhead for AVI container and headers
        avi_overhead = 10 * 1024  # 10KB overhead
        estimated_size = (len(frames) * compressed_frame_size) + avi_overhead
        
        if not self.ensure_storage_available(estimated_size):
            return None
            
        try:
            # Initialize video writer with MJPG codec
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(str(filepath), fourcc, 30.0, (width, height))
            
            if not out.isOpened():
                raise Exception("Failed to initialize video writer")
            
            # Write frames
            for frame in frames:
                out.write(frame)
                
            # Properly release the video writer
            out.release()
            
            logger.info(f"Saved recording to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving recording: {str(e)}")
            if filepath.exists():
                filepath.unlink()
            return None
            
    def get_recordings_list(self) -> list:
        """Get list of recordings with metadata"""
        recordings = []
        try:
            # Ensure directory exists
            if not self.recordings_path.exists():
                self.recordings_path.mkdir(parents=True, exist_ok=True)
                return []
                
            # Get all video files
            video_files = list(self.recordings_path.glob("*.avi")) + list(self.recordings_path.glob("*.mp4"))
            
            for filepath in sorted(video_files, key=lambda x: x.stat().st_mtime, reverse=True):
                try:
                    # Get file stats
                    stats = filepath.stat()
                    size_bytes = stats.st_size
                    
                    # Skip empty or corrupt files
                    if size_bytes == 0:
                        logger.warning(f"Found empty recording file: {filepath}")
                        filepath.unlink()
                        continue
                        
                    # Format size
                    if size_bytes < 1024:
                        size = f"{size_bytes}B"
                    elif size_bytes < 1024 * 1024:
                        size = f"{size_bytes/1024:.1f}KB"
                    else:
                        size = f"{size_bytes/(1024*1024):.1f}MB"
                        
                    # Get timestamp from filename or file modification time
                    try:
                        timestamp = datetime.strptime(filepath.stem, "%Y%m%d_%H%M%S")
                    except ValueError:
                        timestamp = datetime.fromtimestamp(stats.st_mtime)
                    
                    recordings.append({
                        "id": filepath.stem,
                        "filename": filepath.name,
                        "path": str(filepath),
                        "size": size,
                        "size_bytes": size_bytes,
                        "duration": "N/A",  # Skip duration calculation for performance
                        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    })
                except Exception as e:
                    logger.error(f"Error getting metadata for {filepath}: {str(e)}")
                    continue
                    
            return recordings
        except Exception as e:
            logger.error(f"Error listing recordings: {str(e)}")
            return []
        
    def cleanup_failed_recordings(self):
        """Clean up empty or corrupt recording files"""
        try:
            video_files = list(self.recordings_path.glob("*.avi")) + list(self.recordings_path.glob("*.mp4"))
            for filepath in video_files:
                try:
                    # Check if file is empty
                    if filepath.stat().st_size == 0:
                        logger.warning(f"Removing empty recording file: {filepath}")
                        filepath.unlink()
                        continue
                        
                    # Try to open video file
                    cap = cv2.VideoCapture(str(filepath))
                    if not cap.isOpened():
                        logger.warning(f"Removing corrupt recording file: {filepath}")
                        filepath.unlink()
                    cap.release()
                except Exception as e:
                    logger.error(f"Error checking recording file {filepath}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error cleaning up recordings: {str(e)}")
        
    def delete_recording(self, recording_id: str) -> bool:
        """
        Delete a specific recording
        
        Args:
            recording_id: ID of recording to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            for ext in ['.avi', '.mp4']:
                file_path = self.recordings_path / f"{recording_id}{ext}"
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted recording: {file_path.name}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting recording {recording_id}: {str(e)}")
            return False 
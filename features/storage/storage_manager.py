"""
Storage Manager for BirdsOS
Handles disk usage monitoring, storage limits, and video retention.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv, set_key, find_dotenv

class StorageManager:
    """Manages storage for video recordings and system data."""
    
    def __init__(self, 
                 storage_path: str,
                 storage_limit: Optional[int] = None,
                 warning_threshold: Optional[float] = None,
                 retention_days: Optional[int] = None,
                 log_file: str = "storage.log"):
        """
        Initialize the StorageManager.
        
        Args:
            storage_path: Base path for stored files
            storage_limit: Maximum storage in bytes (defaults to env var or 10GB)
            warning_threshold: Percentage at which to warn (defaults to env var or 0.85)
            retention_days: Number of days to retain video files (defaults to env var or 14)
            log_file: Path to log file relative to storage_path
        """
        # Load environment variables
        load_dotenv()
        
        self.storage_path = Path(storage_path)
        
        # Set configuration from parameters or environment variables
        # If a parameter is provided, use it. Otherwise check env vars, then fallback to defaults
        if storage_limit is not None:
            self.storage_limit = storage_limit
        else:
            env_gb = os.getenv('MAX_STORAGE_GB')
            if env_gb:
                # Convert GB to bytes, handling float values
                gb_value = float(env_gb)
                self.storage_limit = int(gb_value * 1024 * 1024 * 1024)
            else:
                self.storage_limit = 10 * 1024 * 1024 * 1024  # 10GB default
            
        if warning_threshold is not None:
            self.warning_threshold = warning_threshold
        else:
            env_threshold = os.getenv('WARNING_THRESHOLD')
            self.warning_threshold = float(env_threshold) if env_threshold else 0.85
            
        if retention_days is not None:
            self.retention_days = retention_days
        else:
            env_days = os.getenv('RETENTION_DAYS')
            self.retention_days = int(env_days) if env_days else 14
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging(log_file)
        
        # Initialize statistics
        self.stats = {
            "total_videos": 0,
            "total_size": 0,
            "oldest_file": None,
            "newest_file": None
        }
        self.update_statistics()
        
        logging.info(f"StorageManager initialized with path: {storage_path}")

    def _setup_logging(self, log_file: str) -> None:
        """Configure logging for storage operations."""
        log_path = self.storage_path / "logs"
        log_path.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=str(log_path / log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _get_directory_size(self) -> int:
        """Calculate total size of managed directory."""
        total_size = 0
        for dirpath, _, filenames in os.walk(str(self.storage_path)):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):  # Skip if it's a symbolic link
                    total_size += os.path.getsize(fp)
        return total_size

    def check_storage(self) -> Dict:
        """
        Check current storage status.
        
        Returns:
            Dict containing storage metrics and warning status
        """
        try:
            # Get total disk space for reference
            total_disk, _, free_disk = shutil.disk_usage(str(self.storage_path))
            
            # Get our directory's usage
            used = self._get_directory_size()
            usage_ratio = used / self.storage_limit
            
            status = {
                "total": self.storage_limit,  # Our allocated limit
                "used": used,
                "free": max(0, self.storage_limit - used),
                "usage_ratio": usage_ratio,
                "warning": usage_ratio > self.warning_threshold,
                "critical": used > self.storage_limit,
                "disk_free": free_disk  # Keep track of actual disk space too
            }
            
            if status["warning"]:
                logging.warning(f"Storage usage high: {usage_ratio:.1%}")
            
            return status
            
        except Exception as e:
            logging.error(f"Error checking storage: {str(e)}")
            raise

    def cleanup_old_files(self) -> bool:
        """
        Remove files beyond retention period or when over storage limit.
        
        Returns:
            bool: True if cleanup was successful
        """
        try:
            # Calculate retention cutoff
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Get all video files sorted by modification time
            video_files = sorted(
                [f for f in self.storage_path.glob("*.mp4") if f.is_file()],
                key=lambda x: x.stat().st_mtime
            )
            
            files_removed = 0
            bytes_freed = 0
            
            # First pass: Remove files beyond retention period
            for video_file in video_files[:]:
                try:
                    mod_time = datetime.fromtimestamp(video_file.stat().st_mtime)
                    if mod_time < cutoff_date:
                        size = video_file.stat().st_size
                        video_file.unlink()
                        video_files.remove(video_file)
                        files_removed += 1
                        bytes_freed += size
                        logging.info(f"Removed old file: {video_file.name}")
                except OSError as e:
                    logging.warning(f"Could not remove file {video_file}: {e}")
                    continue
                    
            # Second pass: Remove oldest files if still over limit
            while self._get_directory_size() > self.storage_limit and video_files:
                try:
                    oldest_file = video_files.pop(0)
                    size = oldest_file.stat().st_size
                    oldest_file.unlink()
                    files_removed += 1
                    bytes_freed += size
                    logging.info(f"Removed file due to storage limit: {oldest_file.name}")
                except OSError as e:
                    logging.warning(f"Could not remove file {oldest_file}: {e}")
                    continue
            
            if files_removed > 0:
                logging.info(f"Cleanup completed: removed {files_removed} files, freed {bytes_freed/1024/1024:.1f}MB")
                self.update_statistics()
                
            return True
            
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            return False

    def update_statistics(self) -> None:
        """Update storage statistics."""
        try:
            video_files = [f for f in self.storage_path.glob("*.mp4") if f.is_file()]
            
            self.stats["total_videos"] = len(video_files)
            self.stats["total_size"] = sum(f.stat().st_size for f in video_files)
            
            if video_files:
                oldest = min(video_files, key=lambda x: x.stat().st_mtime)
                newest = max(video_files, key=lambda x: x.stat().st_mtime)
                self.stats["oldest_file"] = datetime.fromtimestamp(oldest.stat().st_mtime)
                self.stats["newest_file"] = datetime.fromtimestamp(newest.stat().st_mtime)
            else:
                self.stats["oldest_file"] = None
                self.stats["newest_file"] = None
                
        except Exception as e:
            logging.error(f"Error updating statistics: {str(e)}")

    def get_statistics(self) -> Dict:
        """
        Get current storage statistics.
        
        Returns:
            Dict containing storage statistics
        """
        self.update_statistics()
        storage_status = self.check_storage()
        
        return {
            **self.stats,
            "storage_status": storage_status,
            "retention_days": self.retention_days,
            "warning_threshold": self.warning_threshold
        }

    def get_video_files(self) -> List[Dict]:
        """
        Get list of video files with metadata.
        
        Returns:
            List of dicts containing video file information
        """
        try:
            video_files = []
            for video_file in self.storage_path.glob("*.mp4"):
                if not video_file.is_file():
                    continue
                stats = video_file.stat()
                video_files.append({
                    "name": video_file.name,
                    "size": stats.st_size,
                    "created": datetime.fromtimestamp(stats.st_ctime),
                    "modified": datetime.fromtimestamp(stats.st_mtime)
                })
            return sorted(video_files, key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            logging.error(f"Error getting video files: {str(e)}")
            return []

    def save_config(self) -> bool:
        """Save current configuration to environment file and update process environment"""
        try:
            # Validate storage limit against available disk space
            total_disk, _, _ = shutil.disk_usage(str(self.storage_path))
            if self.storage_limit > total_disk:
                raise ValueError("Storage limit cannot exceed total disk space")
            
            # Find the .env file or create it in the project root
            env_path = find_dotenv()
            if not env_path:
                env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
                if not os.path.exists(env_path):
                    with open(env_path, 'w') as f:
                        f.write('# BirdsOS Environment Configuration\n')
            
            # Save configuration values
            gb_value = f"{self.storage_limit / (1024*1024*1024):.1f}"
            set_key(env_path, 'MAX_STORAGE_GB', gb_value)
            set_key(env_path, 'WARNING_THRESHOLD', str(self.warning_threshold))
            set_key(env_path, 'RETENTION_DAYS', str(self.retention_days))
            
            # Update process environment variables
            os.environ['MAX_STORAGE_GB'] = gb_value
            os.environ['WARNING_THRESHOLD'] = str(self.warning_threshold)
            os.environ['RETENTION_DAYS'] = str(self.retention_days)
            
            # Reload environment variables for other processes
            load_dotenv(env_path)
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
            return False

    def update_config(self, storage_limit: int, warning_threshold: float, retention_days: int) -> bool:
        """Update configuration with new values and save to environment file"""
        try:
            self.storage_limit = storage_limit
            self.warning_threshold = warning_threshold
            self.retention_days = retention_days
            return self.save_config()
        except Exception as e:
            logging.error(f"Error updating configuration: {str(e)}")
            return False 
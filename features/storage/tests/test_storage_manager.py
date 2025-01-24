"""
Tests for the StorageManager class
"""

import os
import pytest
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from ..storage_manager import StorageManager
from unittest.mock import patch

@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary directory for storage tests"""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    yield storage_dir
    shutil.rmtree(storage_dir)

@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a StorageManager instance for testing"""
    return StorageManager(
        storage_path=str(temp_storage_dir),
        storage_limit=100 * 1024 * 1024,  # 100MB for testing
        warning_threshold=0.8,
        retention_days=1
    )

def create_test_video(storage_dir: Path, name: str, size: int = 1024, days_old: int = 0):
    """Helper to create a test video file"""
    video_path = storage_dir / f"{name}.mp4"
    with open(video_path, 'wb') as f:
        f.write(b'0' * size)
    
    # Set file modification time
    mtime = datetime.now() - timedelta(days=days_old)
    os.utime(video_path, (mtime.timestamp(), mtime.timestamp()))
    return video_path

def test_init(storage_manager, temp_storage_dir):
    """Test StorageManager initialization"""
    assert storage_manager.storage_path == temp_storage_dir
    assert storage_manager.storage_limit == 100 * 1024 * 1024
    assert storage_manager.warning_threshold == 0.8
    assert storage_manager.retention_days == 1
    assert (temp_storage_dir / "logs").exists()

def test_check_storage(storage_manager, temp_storage_dir):
    """Test storage status checking"""
    # Create some test files
    create_test_video(temp_storage_dir, "test1", size=1024 * 1024)  # 1MB
    create_test_video(temp_storage_dir, "test2", size=1024 * 1024)  # 1MB
    
    status = storage_manager.check_storage()
    assert "total" in status
    assert "used" in status
    assert "free" in status
    assert "warning" in status
    assert not status["warning"]  # Should not warn with just 2MB used

def test_cleanup_old_files(storage_manager, temp_storage_dir):
    """Test cleanup of old files"""
    # Create test files with different ages
    create_test_video(temp_storage_dir, "old", days_old=2)  # Beyond retention
    create_test_video(temp_storage_dir, "new", days_old=0)  # Within retention
    
    assert storage_manager.cleanup_old_files()
    
    # Check that only old file was removed
    remaining_files = list(temp_storage_dir.glob("*.mp4"))
    assert len(remaining_files) == 1
    assert remaining_files[0].name == "new.mp4"

def test_storage_limit_cleanup(storage_manager, temp_storage_dir):
    """Test cleanup when storage limit is exceeded"""
    # Create files that exceed storage limit
    total_size = storage_manager.storage_limit + 1024 * 1024  # Exceed by 1MB
    create_test_video(temp_storage_dir, "big", size=total_size)
    
    assert storage_manager.cleanup_old_files()
    
    # Check that space was freed
    status = storage_manager.check_storage()
    assert status["used"] <= storage_manager.storage_limit

def test_get_statistics(storage_manager, temp_storage_dir):
    """Test statistics gathering"""
    # Create test files
    create_test_video(temp_storage_dir, "test1")
    create_test_video(temp_storage_dir, "test2")
    
    stats = storage_manager.get_statistics()
    assert stats["total_videos"] == 2
    assert stats["total_size"] > 0
    assert stats["oldest_file"] is not None
    assert stats["newest_file"] is not None
    assert "storage_status" in stats
    assert "retention_days" in stats
    assert "warning_threshold" in stats

def test_get_video_files(storage_manager, temp_storage_dir):
    """Test video file listing"""
    # Create test files
    create_test_video(temp_storage_dir, "test1")
    create_test_video(temp_storage_dir, "test2")
    
    video_files = storage_manager.get_video_files()
    assert len(video_files) == 2
    for video in video_files:
        assert "name" in video
        assert "size" in video
        assert "created" in video
        assert "modified" in video
    
    # Check sorting (newest first)
    assert video_files[0]["modified"] >= video_files[1]["modified"]

def test_config_persistence(storage_manager, temp_storage_dir, tmp_path):
    """Test that configuration is properly persisted to .env file"""
    # Create a temporary .env file for testing
    env_file = tmp_path / '.env'
    with open(env_file, 'w') as f:
        f.write('# Test environment file\n')
    
    # Set new configuration values
    storage_gb = 0.2  # 200MB in GB
    new_config = {
        'storage_limit': int(storage_gb * 1024 * 1024 * 1024),  # Convert GB to bytes
        'warning_threshold': 0.75,
        'retention_days': 7
    }
    
    # Mock both find_dotenv and load_dotenv
    with patch('features.storage.storage_manager.find_dotenv', return_value=str(env_file)), \
         patch('features.storage.storage_manager.load_dotenv') as mock_load_dotenv:
        
        def mock_load_env(*args, **kwargs):
            # Set environment variables manually
            os.environ['MAX_STORAGE_GB'] = str(storage_gb)
            os.environ['WARNING_THRESHOLD'] = str(new_config['warning_threshold'])
            os.environ['RETENTION_DAYS'] = str(new_config['retention_days'])
        
        mock_load_dotenv.side_effect = mock_load_env
        
        # Update and save configuration
        assert storage_manager.update_config(
            storage_limit=new_config['storage_limit'],
            warning_threshold=new_config['warning_threshold'],
            retention_days=new_config['retention_days']
        )
        
        # Create a new instance to verify values are loaded from .env
        new_manager = StorageManager(
            str(temp_storage_dir),
            storage_limit=None,  # Force loading from env
            warning_threshold=None,
            retention_days=None
        )
        
        # Verify configuration was persisted
        assert new_manager.storage_limit == new_config['storage_limit'], \
            f"Expected {new_config['storage_limit']} bytes, got {new_manager.storage_limit} bytes"
        assert new_manager.warning_threshold == new_config['warning_threshold']
        assert new_manager.retention_days == new_config['retention_days']
        
        # Verify values in .env file
        with open(env_file) as f:
            env_contents = f.read()
            assert f"MAX_STORAGE_GB='{storage_gb}'" in env_contents
            assert f"WARNING_THRESHOLD='{new_config['warning_threshold']}'" in env_contents
            assert f"RETENTION_DAYS='{new_config['retention_days']}'" in env_contents 
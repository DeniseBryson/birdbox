"""
Shared test fixtures for storage feature tests
"""

import pytest
import shutil
from pathlib import Path

@pytest.fixture(scope="session")
def test_storage_root(tmp_path_factory):
    """Create a root test storage directory for the entire test session"""
    root_dir = tmp_path_factory.mktemp("storage_test_root")
    yield root_dir
    shutil.rmtree(root_dir)

@pytest.fixture
def mock_video_file(test_storage_root):
    """Create a mock video file for testing"""
    def _create_video(name: str, size: int = 1024):
        video_path = test_storage_root / f"{name}.mp4"
        with open(video_path, 'wb') as f:
            f.write(b'0' * size)
        return video_path
    return _create_video 
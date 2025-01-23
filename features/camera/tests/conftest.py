"""
Test configuration for camera feature
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch

@pytest.fixture(autouse=True)
def mock_cv2():
    """Mock cv2 for all tests"""
    with patch('cv2.VideoCapture') as mock_cap:
        # Setup default mock behavior
        mock_cap.return_value.isOpened.return_value = True
        mock_cap.return_value.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))
        mock_cap.return_value.set.return_value = True
        mock_cap.return_value.release.return_value = None
        yield mock_cap 
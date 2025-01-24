"""
Tests for system version management and updates
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import time
import signal

def test_get_version(client):
    """Test getting current version info"""
    with patch('routes.system_routes.get_git_info') as mock_git:
        mock_git.return_value = {
            'commit_hash': 'abc1234',
            'commit_date': '2024-03-20 10:00:00'
        }
        
        response = client.get('/api/v1/system/version')
        assert response.status_code == 200
        data = response.json
        assert 'commit_hash' in data
        assert 'commit_date' in data

def test_check_update_available(client):
    """Test checking for available updates"""
    with patch('routes.system_routes.check_remote_updates') as mock_check:
        mock_check.return_value = (True, ['Fix: Bug in storage', 'Add: New feature'])
        
        response = client.get('/api/v1/system/check-update')
        assert response.status_code == 200
        data = response.json
        assert data['update_available'] is True
        assert len(data['changes']) == 2

def test_check_update_not_available(client):
    """Test checking when no updates available"""
    with patch('routes.system_routes.check_remote_updates') as mock_check:
        mock_check.return_value = (False, [])
        
        response = client.get('/api/v1/system/check-update')
        assert response.status_code == 200
        data = response.json
        assert data['update_available'] is False
        assert len(data['changes']) == 0

def test_apply_update_success(client):
    """Test successful update application"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        
        response = client.post('/api/v1/system/update')
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

def test_apply_update_failure(client):
    """Test failed update application"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception('Update failed')
        
        response = client.post('/api/v1/system/update')
        assert response.status_code == 500
        data = response.json
        assert data['status'] == 'error'
        assert 'Update failed' in data['message']

def test_git_info_error_handling():
    """Test git info error handling"""
    with patch('subprocess.check_output') as mock_output:
        mock_output.side_effect = Exception('Git error')
        
        from routes.system_routes import get_git_info
        info = get_git_info()
        assert info['commit_hash'] == 'unknown'
        assert datetime.fromisoformat(info['commit_date'])

def test_version_info_complete(client):
    """Test that version info includes all required fields"""
    with patch('routes.system_routes.subprocess.check_output') as mock_output:
        def mock_git_command(cmd, **kwargs):
            if 'rev-parse' in cmd and '--abbrev-ref' in cmd:
                return b'AIgen2\n'
            elif 'rev-parse' in cmd:
                return b'abc1234def5678\n'
            elif 'show' in cmd:
                return b'2024-03-20 10:00:00 +0000\n'
            raise ValueError(f"Unexpected command: {cmd}")
        
        mock_output.side_effect = mock_git_command
        
        response = client.get('/api/v1/system/version')
        assert response.status_code == 200
        data = response.json
        
        assert 'commit_hash' in data
        assert 'commit_date' in data
        assert 'branch' in data
        assert data['branch'] == 'AIgen2'
        assert len(data['commit_hash']) == 14  # Full commit hash length

def test_reload_server(client):
    """Test server reload endpoint"""
    with patch('routes.system_routes.os.kill') as mock_kill, \
         patch('routes.system_routes.os.getpid', return_value=12345):
        
        response = client.post('/api/v1/system/reload')
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        
        # Wait for the timer to trigger the restart
        time.sleep(1.1)
        
        # Verify the kill signal was sent
        mock_kill.assert_called_once_with(12345, signal.SIGTERM)

def test_settings_persistence(client):
    """Test that settings changes persist and can be reloaded"""
    # Set initial configuration
    initial_config = {
        'storage_limit': 5 * 1024 * 1024 * 1024,  # 5GB
        'warning_threshold': 0.75,
        'retention_days': 7
    }
    
    response = client.post('/api/v1/config/storage', 
                          json=initial_config,
                          content_type='application/json')
    assert response.status_code == 200
    
    # Verify settings were saved
    response = client.get('/api/v1/config/storage')
    assert response.status_code == 200
    data = response.json
    assert data['storage_limit'] == initial_config['storage_limit']
    assert data['warning_threshold'] == initial_config['warning_threshold']
    assert data['retention_days'] == initial_config['retention_days']
    
    # Update configuration
    new_config = {
        'storage_limit': 8 * 1024 * 1024 * 1024,  # 8GB
        'warning_threshold': 0.85,
        'retention_days': 14
    }
    
    response = client.post('/api/v1/config/storage', 
                          json=new_config,
                          content_type='application/json')
    assert response.status_code == 200
    
    # Trigger server reload
    with patch('routes.system_routes.os.kill'), \
         patch('routes.system_routes.os.getpid', return_value=12345):
        response = client.post('/api/v1/system/reload')
        assert response.status_code == 200
    
    # Verify new settings persisted
    response = client.get('/api/v1/config/storage')
    assert response.status_code == 200
    data = response.json
    assert data['storage_limit'] == new_config['storage_limit']
    assert data['warning_threshold'] == new_config['warning_threshold']
    assert data['retention_days'] == new_config['retention_days'] 
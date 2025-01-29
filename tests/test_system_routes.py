"""
Tests for system version management and updates
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import time
import signal
import subprocess

def test_get_version(client):
    """Test getting current version info"""
    test_hash = 'abc1234'
    test_date = '2024-03-20 10:00:00'
    test_branch = 'main'
    
    with patch('routes.system_routes.get_git_info') as mock_git:
        mock_git.return_value = {
            'commit_hash': test_hash,
            'commit_date': test_date,
            'branch': test_branch
        }
        
        response = client.get('/api/v1/system/version')
        assert response.status_code == 200
        data = response.json
        
        assert 'commit_hash' in data
        assert data['commit_hash'] == test_hash
        assert 'commit_date' in data
        assert data['commit_date'] == test_date
        assert 'branch' in data
        assert data['branch'] == test_branch

def test_get_version_uninitialized(client):
    """Test getting version info when git is not initialized"""
    with patch('routes.system_routes.get_git_info') as mock_git:
        mock_git.side_effect = subprocess.CalledProcessError(128, 'git rev-parse HEAD')
        
        response = client.get('/api/v1/system/version')
        assert response.status_code == 200
        data = response.json
        
        assert data['commit_hash'] == 'uninitialized'
        assert 'commit_date' in data
        assert data['branch'] == 'main'

def test_get_version_error(client):
    """Test getting version info when an unexpected error occurs"""
    with patch('routes.system_routes.get_git_info') as mock_git:
        mock_git.side_effect = Exception("Unexpected error")
        
        response = client.get('/api/v1/system/version')
        assert response.status_code == 200
        data = response.json
        
        assert data['commit_hash'] == 'error'
        assert 'commit_date' in data
        assert data['branch'] == 'unknown'

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

def test_check_update_error(client):
    """Test error handling when checking for updates"""
    with patch('routes.system_routes.check_remote_updates') as mock_check:
        mock_check.side_effect = RuntimeError("Failed to fetch updates")
        
        response = client.get('/api/v1/system/check-update')
        assert response.status_code == 500
        data = response.json
        assert data['status'] == 'error'
        assert 'Failed to fetch updates' in data['message']

def test_apply_update_success(client):
    """Test successful system update"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        
        response = client.post('/api/v1/system/update')
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert 'Update applied successfully' in data['message']
        
        # Verify all required commands were called
        calls = [call[0][0] for call in mock_run.call_args_list]
        assert ['git', 'pull', 'origin', 'AIgen2'] in calls
        assert ['pip', 'install', '-r', 'requirements.txt'] in calls
        assert ['sudo', 'systemctl', 'restart', 'birdbox'] in calls

def test_apply_update_git_error(client):
    """Test handling git errors during update"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git pull', output=b'Failed to pull updates'
        )
        
        response = client.post('/api/v1/system/update')
        assert response.status_code == 500
        data = response.json
        assert data['status'] == 'error'
        assert 'Update failed' in data['message']
        assert 'Failed to pull updates' in data['message']

def test_apply_update_pip_error(client):
    """Test handling pip errors during update"""
    def mock_run_with_pip_error(*args, **kwargs):
        if args[0][0] == 'pip':
            raise subprocess.CalledProcessError(
                1, 'pip install', output=b'Failed to install dependencies'
            )
        return MagicMock(returncode=0)
    
    with patch('subprocess.run', side_effect=mock_run_with_pip_error):
        response = client.post('/api/v1/system/update')
        assert response.status_code == 500
        data = response.json
        assert data['status'] == 'error'
        assert 'Update failed' in data['message']
        assert 'Failed to install dependencies' in data['message']

def test_apply_update_restart_error(client):
    """Test handling service restart errors during update"""
    def mock_run_with_restart_error(*args, **kwargs):
        if args[0][0] == 'sudo':
            raise subprocess.CalledProcessError(
                1, 'systemctl restart', output=b'Failed to restart service'
            )
        return MagicMock(returncode=0)
    
    with patch('subprocess.run', side_effect=mock_run_with_restart_error):
        response = client.post('/api/v1/system/update')
        assert response.status_code == 500
        data = response.json
        assert data['status'] == 'error'
        assert 'Update failed' in data['message']
        assert 'Failed to restart service' in data['message']

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
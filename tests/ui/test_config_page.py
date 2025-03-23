"""
UI tests for the configuration page
Tests the presence and structure of configuration components
"""

import pytest
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv

def test_config_page_loads(client):
    """Test that configuration page loads successfully"""
    response = client.get('/config')
    assert response.status_code == 200
    assert b'System Configuration' in response.data

def test_storage_config_component_present(client):
    """Test that storage configuration component is present with all required elements"""
    response = client.get('/config')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check main component structure
    card = soup.find('div', {'class': 'card'})
    assert card is not None, "Storage configuration card not found"
    
    card_title = card.find('h5', {'class': 'card-title'})
    assert card_title is not None, "Card title not found"
    assert card_title.text == 'Storage Configuration'

def test_storage_config_form_elements(client):
    """Test that all form elements are present with correct attributes"""
    response = client.get('/config')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check form
    form = soup.find('form', id='storage-config-form')
    assert form is not None, "Storage config form not found"
    
    # Check storage limit input group
    storage_limit = form.find('input', id='storage-limit')
    assert storage_limit is not None, "Storage limit input not found"
    assert storage_limit.get('type') == 'number'
    assert storage_limit.get('min') == '1'
    assert storage_limit.get('required') is not None
    
    storage_unit = form.find('select', id='storage-unit')
    assert storage_unit is not None, "Storage unit select not found"
    units = [option.text for option in storage_unit.find_all('option')]
    assert 'GB' in units and 'MB' in units, "Storage units options missing"
    
    # Check warning threshold input
    threshold = form.find('input', id='warning-threshold')
    assert threshold is not None, "Warning threshold input not found"
    assert threshold.get('type') == 'number'
    assert threshold.get('min') == '50'
    assert threshold.get('max') == '95'
    assert threshold.get('value') == '85'
    
    # Check retention days input
    retention = form.find('input', id='retention-days')
    assert retention is not None, "Retention days input not found"
    assert retention.get('type') == 'number'
    assert retention.get('min') == '1'
    assert retention.get('max') == '365'

def test_storage_info_section(client):
    """Test that storage information section is present with all elements"""
    response = client.get('/config')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check info section
    info_section = soup.find('div', {'class': 'card bg-light'})
    assert info_section is not None, "Storage info section not found"
    
    # Check disk info elements
    disk_info = soup.find('p', id='disk-info')
    assert disk_info is not None, "Disk info element not found"
    assert disk_info.text == 'Loading disk information...'
    
    # Check progress bar
    progress = soup.find('div', {'class': 'progress'})
    assert progress is not None, "Progress bar container not found"
    
    progress_bar = progress.find('div', id='disk-usage')
    assert progress_bar is not None, "Progress bar not found"
    assert 'progress-bar' in progress_bar.get('class', [])
    assert progress_bar.get('role') == 'progressbar'

def test_javascript_inclusion(client):
    """Test that required JavaScript files are included"""
    response = client.get('/config')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for storage config script
    script = soup.find('script', {'src': lambda x: x and 'storage_config.js' in x})
    assert script is not None, "Storage configuration JavaScript not included"
    assert script.get('type') == 'module', "Script should be a module"

def test_storage_warning_triggers(client):
    """Test that storage warnings are triggered appropriately"""
    # Get current storage status
    response = client.get('/api/v1/maintenance/storage/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check warning states
    storage = data['storage']['storage_status']
    usage_ratio = storage['used'] / storage['total']
    
    if usage_ratio > 0.85:
        assert storage['warning'] is True, "Warning should be triggered above 85%"
    else:
        assert storage['warning'] is False, "Warning should not be triggered below 85%"

def test_storage_config_persistence(client, tmp_path):
    """Test that storage configuration is properly persisted"""
    # Set new configuration
    test_config = {
        'storage_limit': 5 * 1024 * 1024 * 1024,  # 5GB
        'warning_threshold': 0.75,
        'retention_days': 7
    }
    
    response = client.post('/api/v1/config/storage', 
                          json=test_config,
                          content_type='application/json')
    assert response.status_code == 200
    
    # Verify configuration was saved
    load_dotenv()
    assert float(os.getenv('MAX_STORAGE_GB')) == 5.0
    assert float(os.getenv('WARNING_THRESHOLD')) == 0.75
    assert int(os.getenv('RETENTION_DAYS')) == 7
    
    # Verify configuration is loaded correctly
    response = client.get('/api/v1/config/storage')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['storage_limit'] == test_config['storage_limit']
    assert data['warning_threshold'] == test_config['warning_threshold']
    assert data['retention_days'] == test_config['retention_days'] 
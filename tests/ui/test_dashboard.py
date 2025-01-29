"""
UI tests for the dashboard page
Tests the presence and structure of dashboard components
"""

import pytest
from bs4 import BeautifulSoup
from flask import url_for

def test_dashboard_loads(client):
    """Test that dashboard page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_storage_status_section_present(client):
    """Test that storage status section is present with all required elements"""
    response = client.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check storage status card exists
    storage_card = soup.find('h5', {'class': 'card-title'}, string='Storage Status')
    assert storage_card is not None, "Storage status card not found"
    
    # Check progress bar
    progress_bar = soup.find('div', id='storage-progress')
    assert progress_bar is not None, "Storage progress bar not found"
    assert 'progress-bar' in progress_bar.get('class', [])
    
    # Check storage details elements
    storage_details = soup.find('p', id='storage-details')
    assert storage_details is not None, "Storage details element not found"
    assert "Loading storage details..." in storage_details.text
    
    storage_warning = soup.find('p', id='storage-warning')
    assert storage_warning is not None, "Storage warning element not found"
    assert "Storage usage is high!" in storage_warning.text
    
    # Check video section
    video_stats = soup.find('p', id='video-stats')
    assert video_stats is not None, "Video stats element not found"
    assert "Loading video statistics..." in video_stats.text
    
    video_list = soup.find('div', id='video-list')
    assert video_list is not None, "Video list element not found"
    assert "Loading recent videos..." in video_list.text

def test_storage_status_script_included(client):
    """Test that storage status JavaScript is included"""
    response = client.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    script_tag = soup.find('script', src=lambda x: x and 'storage_status.js' in x)
    assert script_tag is not None, "Storage status JavaScript not included"

@pytest.mark.parametrize('expected_card_title', [
    'System Status',
    'Camera Status',
    'Food Level'
])
def test_status_cards_present(client, expected_card_title):
    """Test that all status cards are present"""
    response = client.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    card = soup.find('h5', {'class': 'card-title'}, string=expected_card_title)
    assert card is not None, f"{expected_card_title} card not found"

def test_version_info_section_present(client):
    """Test that version information section is present with all required elements"""
    response = client.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check version info card exists
    version_card = soup.find('h5', {'class': 'card-title'}, string='System Version')
    assert version_card is not None, "Version info card not found"
    
    # Check version elements
    commit_hash = soup.find('code', id='commit-hash')
    assert commit_hash is not None, "Commit hash element not found"
    
    commit_date = soup.find('small', id='commit-date')
    assert commit_date is not None, "Commit date element not found"
    
    # Check update elements
    check_button = soup.find('button', id='check-update')
    assert check_button is not None, "Check for updates button not found"
    assert "Check for Updates" in check_button.text
    
    update_status = soup.find('p', id='update-status')
    assert update_status is not None, "Update status element not found"
    
    # Check update info section
    update_info = soup.find('div', id='update-info')
    assert update_info is not None, "Update info section not found"
    assert "d-none" in update_info.get('class', []), "Update info should be hidden by default"
    
    update_changes = soup.find('pre', id='update-changes')
    assert update_changes is not None, "Update changes element not found"

def test_version_script_included(client):
    """Test that version manager JavaScript is included"""
    response = client.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')
    
    script_tag = soup.find('script', src=lambda x: x and 'version_manager.js' in x)
    assert script_tag is not None, "Version manager JavaScript not included" 
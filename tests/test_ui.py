import pytest
from app import app

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestUI:
    def test_dashboard_ui(self, client):
        """Test dashboard page UI"""
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode()
        assert "Dashboard - BirdsOS" in html
        assert "<h1>Dashboard</h1>" in html
        assert "System Status" in html
        assert "Camera Status" in html
        assert "Food Level" in html
        
    def test_camera_ui(self, client):
        """Test camera page UI"""
        response = client.get('/camera')
        assert response.status_code == 200
        html = response.data.decode()
        assert "Camera - BirdsOS" in html
        assert "<h1>Camera Control</h1>" in html
        assert 'id="camera-feed"' in html
        assert 'id="start-recording"' in html
        assert 'id="stop-recording"' in html
        
    def test_hardware_ui(self, client):
        """Test hardware page UI"""
        response = client.get('/hardware')
        assert response.status_code == 200
        html = response.data.decode()
        assert "Hardware Control - BirdsOS" in html
        assert "<h1>Hardware Control</h1>" in html
        assert 'id="gpio-status"' in html
        assert 'id="motor-status"' in html
        
    def test_config_ui(self, client):
        """Test config page UI"""
        response = client.get('/config')
        assert response.status_code == 200
        html = response.data.decode()
        assert "Configuration - BirdsOS" in html
        assert "<h1>System Configuration</h1>" in html
        assert 'id="profiles-list"' in html
        assert 'id="settings-panel"' in html
        
    def test_maintenance_ui(self, client):
        """Test maintenance page UI"""
        response = client.get('/maintenance')
        assert response.status_code == 200
        html = response.data.decode()
        assert "Maintenance - BirdsOS" in html
        assert "<h1>System Maintenance</h1>" in html
        assert 'id="food-level"' in html
        assert 'id="storage-status"' in html
        
    def test_analytics_ui(self, client):
        """Test analytics page UI"""
        response = client.get('/analytics')
        assert response.status_code == 200
        html = response.data.decode()
        assert "Analytics - BirdsOS" in html
        assert "<h1>System Analytics</h1>" in html
        assert 'id="visit-stats"' in html
        assert 'id="feeding-patterns"' in html
        
    def test_navigation_links(self, client):
        """Test that all navigation links are present"""
        response = client.get('/')
        html = response.data.decode()
        nav_links = [
            ('Dashboard', '/'),
            ('Camera', '/camera'),
            ('Hardware', '/hardware'),
            ('Config', '/config'),
            ('Maintenance', '/maintenance'),
            ('Analytics', '/analytics')
        ]
        for text, href in nav_links:
            assert f'href="{href}"' in html
            assert text in html
            
    def test_error_handling(self, client):
        """Test error handling for non-existent pages"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        html = response.data.decode()
        assert "404" in html
        assert "Page Not Found" in html 
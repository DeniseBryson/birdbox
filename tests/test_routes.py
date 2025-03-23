import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test Main Routes
def test_dashboard_route(client):
    """Test dashboard route"""
    rv = client.get('/')
    assert rv.status_code == 200

def test_camera_route(client):
    """Test camera route with and without trailing slash"""
    rv = client.get('/camera')
    assert rv.status_code == 200
    rv = client.get('/camera/')
    assert rv.status_code == 200

def test_hardware_route(client):
    """Test hardware route with and without trailing slash"""
    rv = client.get('/hardware')
    assert rv.status_code == 200
    rv = client.get('/hardware/')
    assert rv.status_code == 200

def test_config_route(client):
    """Test config route with and without trailing slash"""
    rv = client.get('/config')
    assert rv.status_code == 200
    rv = client.get('/config/')
    assert rv.status_code == 200

def test_maintenance_route(client):
    """Test maintenance route with and without trailing slash"""
    rv = client.get('/maintenance')
    assert rv.status_code == 200
    rv = client.get('/maintenance/')
    assert rv.status_code == 200

def test_analytics_route(client):
    """Test analytics route with and without trailing slash"""
    rv = client.get('/analytics')
    assert rv.status_code == 200
    rv = client.get('/analytics/')
    assert rv.status_code == 200

# Test API Routes
def test_system_status_api(client):
    """Test system status API"""
    rv = client.get('/api/v1/system/status')
    assert rv.status_code == 200
    assert rv.json['status'] == 'operational'

def test_camera_stream_api(client):
    """Test camera stream API"""
    rv = client.get('/api/v1/camera/stream')
    assert rv.status_code == 200
    assert 'stream_url' in rv.json

def test_hardware_gpio_status_api(client):
    """Test GPIO status API"""
    rv = client.get('/api/v1/hardware/gpio/status')
    assert rv.status_code == 200
    assert 'gpio' in rv.json

def test_config_profiles_api(client):
    """Test config profiles API"""
    rv = client.get('/api/v1/config/profiles')
    assert rv.status_code == 200
    assert 'profiles' in rv.json

def test_maintenance_food_level_api(client):
    """Test food level API"""
    rv = client.get('/api/v1/maintenance/food-level')
    assert rv.status_code == 200
    assert 'food_level' in rv.json

def test_analytics_statistics_api(client):
    """Test analytics statistics API"""
    rv = client.get('/api/v1/analytics/statistics')
    assert rv.status_code == 200
    assert 'statistics' in rv.json 
"""
Test configuration and fixtures for GPIO tests
"""
from flask.testing import FlaskClient
import pytest
from flask import Flask
from unittest.mock import patch
from features.gpio.routes import gpio_bp
from features.gpio.manager import GPIOManager
import RPi.GPIO as RPI_GPIO

@pytest.fixture(scope='session', autouse=True)
def setup_gpio_session():
    """Setup GPIO mode for the test session."""
    try:
        # Clean up any existing configuration
        RPI_GPIO.cleanup()
        # Set mode to BCM for the entire test session
        RPI_GPIO.setmode(RPI_GPIO.BCM)
        RPI_GPIO.setwarnings(False)
        yield
    finally:
        try:
            # Clean up at the end of the session
            RPI_GPIO.cleanup()
        except:
            pass

@pytest.fixture
def gpio_manager():
    """Create a fresh GPIO manager for each test."""
    manager = GPIOManager()
    yield manager
    try:
        manager.cleanup()
    except:
        pass  # Ignore cleanup errors in tests

@pytest.fixture
def mock_gpio():
    """Mock GPIO hardware interface for all tests."""
    with patch('features.gpio.hardware.GPIO') as mock:
        # Set up default behavior
        mock.IN = "IN"
        mock.OUT = "OUT"
        mock.HIGH = 1
        mock.LOW = 0
        mock.VALID_PINS = [18, 23, 24, 25, 8, 7, 12, 16, 20, 21]
        yield mock

@pytest.fixture
def app(gpio_manager: GPIOManager) -> Flask:
    """Create test Flask application."""
    app = Flask(__name__,
                template_folder='templates',    # Use root templates directory
                static_folder='static')         # Use root static directory
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost:5001'  # Use different port for testing
    app.register_blueprint(gpio_bp, url_prefix='/gpio')
    return app

@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app: Flask):
    """Create test CLI runner."""
    return app.test_cli_runner() 
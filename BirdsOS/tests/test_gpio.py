"""
Tests for GPIO functionality
"""
import unittest
from flask import json
from app import app
from src.hardware import GPIO

class TestGPIO(unittest.TestCase):
    def setUp(self):
        """Set up test client and initialize GPIO"""
        self.app = app.test_client()
        self.app.testing = True
        GPIO.setmode(GPIO.BCM)
        
    def tearDown(self):
        """Clean up after each test"""
        GPIO.cleanup()
        
    def test_gpio_status_endpoint(self):
        """Test GPIO status endpoint returns correct pin states"""
        # Setup test pins
        GPIO.setup(24, GPIO.IN)  # Optical Gate 1
        GPIO.setup(25, GPIO.IN)  # Optical Gate 2
        
        response = self.app.get('/api/gpio/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['mode'], 'BCM')
        self.assertIn('24', str(data['pins']))  # Convert to string to handle integer keys
        self.assertIn('25', str(data['pins']))
        
    def test_gpio_trigger_endpoint(self):
        """Test GPIO trigger endpoint changes pin states"""
        # Setup test pin
        GPIO.setup(24, GPIO.IN)
        
        # Trigger pin HIGH
        response = self.app.post('/api/gpio/trigger',
                               json={'pin': 24, 'state': 1})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        
        # Verify pin state
        status_response = self.app.get('/api/gpio/status')
        status_data = json.loads(status_response.data)
        self.assertEqual(status_data['pins']['24']['state'], 1)
        
        # Trigger pin LOW
        response = self.app.post('/api/gpio/trigger',
                               json={'pin': 24, 'state': 0})
        self.assertEqual(response.status_code, 200)
        
        # Verify pin state changed
        status_response = self.app.get('/api/gpio/status')
        status_data = json.loads(status_response.data)
        self.assertEqual(status_data['pins']['24']['state'], 0)
        
    def test_invalid_pin_trigger(self):
        """Test triggering an invalid pin returns error"""
        response = self.app.post('/api/gpio/trigger',
                               json={'pin': 999, 'state': 1})
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        
    def test_missing_parameters(self):
        """Test trigger endpoint with missing parameters"""
        response = self.app.post('/api/gpio/trigger',
                               json={'pin': 24})  # Missing state
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        
    def test_gpio_simulator_page(self):
        """Test GPIO simulator page loads correctly"""
        response = self.app.get('/gpio')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'GPIO Simulator', response.data)

if __name__ == '__main__':
    unittest.main() 
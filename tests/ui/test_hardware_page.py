"""UI tests for hardware page using Flask test client."""

import unittest
from bs4 import BeautifulSoup
from app import create_app

class TestHardwarePage(unittest.TestCase):
    """Test cases for hardware page UI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_page_elements(self):
        """Test presence of required page elements."""
        response = self.client.get('/hardware/')
        self.assertEqual(response.status_code, 200)
        
        # Parse HTML
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Check title
        title = soup.find('h1')
        self.assertIsNotNone(title)
        self.assertEqual(title.text, 'Hardware Control')
        
        # Check GPIO section
        gpio_status = soup.find(id='gpio-status')
        self.assertIsNotNone(gpio_status)
        self.assertEqual(gpio_status.text, 'Loading GPIO status...')
        
        # Check GPIO page link
        gpio_link = soup.find(id='gpio-page-link')
        self.assertIsNotNone(gpio_link)
        self.assertEqual(gpio_link.text, 'GPIO Control Page')
        self.assertEqual(gpio_link['href'], '/gpio/')
        
        # Check motor section
        motor_status = soup.find(id='motor-status')
        self.assertIsNotNone(motor_status)
        self.assertEqual(motor_status.text, 'Loading motor status...')
    
    def test_gpio_page_accessible(self):
        """Test that GPIO page is accessible from hardware page."""
        # First verify the link on hardware page
        hardware_response = self.client.get('/hardware/')
        self.assertEqual(hardware_response.status_code, 200)
        
        # Parse and verify GPIO link
        soup = BeautifulSoup(hardware_response.data, 'html.parser')
        gpio_link = soup.find(id='gpio-page-link')
        self.assertIsNotNone(gpio_link)
        
        # Follow the GPIO link
        gpio_response = self.client.get(gpio_link['href'])
        self.assertEqual(gpio_response.status_code, 200)
        
        # Verify GPIO page content
        gpio_soup = BeautifulSoup(gpio_response.data, 'html.parser')
        title = gpio_soup.find('h1')
        self.assertIsNotNone(title)
        self.assertTrue('GPIO' in title.text)

if __name__ == '__main__':
    unittest.main() 
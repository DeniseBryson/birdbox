import unittest
from unittest.mock import patch
from src.hardware.motor_controller import MotorController

class TestMotorController(unittest.TestCase):
    @patch('RPi.GPIO')
    def test_motor_initialization(self, mock_gpio):
        controller = MotorController()
        # Add your tests here

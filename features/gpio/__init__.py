"""
GPIO Feature Package

This package provides GPIO control functionality for the BirdsOS project.
It includes hardware abstraction, API endpoints, and real-time updates via WebSocket.
"""

from .manager import GPIOManager
from .routes import gpio_bp
from .websocket import sock

__all__ = ['GPIOManager', 'gpio_bp', 'sock']

# Version info
__version__ = '1.0.0' 
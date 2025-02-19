"""
BirdsOS - Main Application Entry Point
"""
from flask import Flask, render_template, jsonify
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from routes.system_routes import system_bp
from features.gpio.routes import gpio_bp, sock as gpio_sock
from features.camera.routes import camera_bp
from features.camera.ws_routes import ws_bp, sock as camera_sock

import os
import logging
from config.logging import setup_logging

def verify_logging():
    """Verify that all major components have logging configured"""
    test_loggers = [
        'app',
        'features.camera',
        'features.gpio',
        'features.storage',
        'routes.main_routes',
        'routes.api_routes',
        'routes.system_routes'
    ]
    
    for logger_name in test_loggers:
        logger = logging.getLogger(logger_name)
        logger.info(f"Logging verification for {logger_name}")

# Set up logging configuration
setup_logging()
logger = logging.getLogger(__name__)

# Verify logging is working across all components
verify_logging()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    logger.info("Initializing BirdsOS application")
    
    # Initialize WebSocket
    gpio_sock.init_app(app, )
    #camera_sock.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(ws_bp, url_prefix='/ws')
    app.register_blueprint(gpio_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(system_bp)
    
    logger.info("All blueprints registered successfully")
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e: Exception):
        logger.warning(f"404 error: {str(e)}")
        return render_template('404.html'), 404
    
    @app.route('/health')
    # TODO: Add more comprehensive health checks
    def health_check():
        """Simple health check endpoint for setup verification."""
        logger.debug("Health check requested")
        return jsonify({"status": "healthy"}), 200
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('recordings', exist_ok=True)
    
    logger.info("Starting BirdsOS in development mode")
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True) 
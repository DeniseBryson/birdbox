"""
BirdsOS - Main Application Entry Point
"""
from flask import Flask, render_template
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from features.gpio.routes import gpio_bp
from features.camera.routes import camera_bp
from features.camera.ws_routes import ws_bp, sock
import os

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize WebSocket
    sock.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(ws_bp, url_prefix='/ws')
    app.register_blueprint(gpio_bp)
    app.register_blueprint(camera_bp)
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('recordings', exist_ok=True)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True) 
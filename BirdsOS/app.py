"""
BirdsOS - Main Application
"""
from flask import Flask, render_template
from src.utils.logger import setup_logger
from config.default import *

app = Flask(__name__)
app.config.from_object('config.default')
logger = setup_logger()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    # TODO: Implement status endpoint
    return {'status': 'operational'}

if __name__ == '__main__':
    logger.info("Starting BirdsOS...")
    app.run(host=HOST, port=PORT, debug=DEBUG)

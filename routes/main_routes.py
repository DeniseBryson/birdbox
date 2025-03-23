"""
STABLE
Main route implementations for BirdsOS
Contains all UI route definitions
Last verified: Current
"""
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    """Main dashboard view"""
    return render_template('dashboard.html')

@main_bp.route('/camera/')
@main_bp.route('/camera')
def camera():
    """Camera management view"""
    return render_template('camera.html')

@main_bp.route('/hardware/')
@main_bp.route('/hardware')
def hardware():
    """Hardware control view"""
    return render_template('hardware.html')

@main_bp.route('/config/')
@main_bp.route('/config')
def config():
    """System configuration view"""
    return render_template('config.html')

@main_bp.route('/maintenance/')
@main_bp.route('/maintenance')
def maintenance():
    """System maintenance view"""
    return render_template('maintenance.html')

@main_bp.route('/analytics/')
@main_bp.route('/analytics')
def analytics():
    """Analytics and statistics view"""
    return render_template('analytics.html') 
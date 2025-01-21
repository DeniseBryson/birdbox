from flask import Blueprint, jsonify
import subprocess
import os

system_bp = Blueprint('system', __name__)

@system_bp.route('/api/system/update', methods=['POST'])
def update_system():
    try:
        # Get the directory where the application is installed
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Pull latest changes
        git_output = subprocess.check_output(['git', 'pull'], cwd=app_dir, stderr=subprocess.STDOUT)
        
        # Check if there were any changes
        if b'Already up to date' in git_output:
            return jsonify({
                'status': 'success',
                'message': 'System is already up to date.'
            })
        
        # Install/update dependencies
        subprocess.check_output(['pip', 'install', '-r', 'requirements.txt'], cwd=app_dir)
        
        return jsonify({
            'status': 'success',
            'message': 'System updated successfully. Please restart the application for changes to take effect.'
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            'status': 'error',
            'message': f'Update failed: {e.output.decode()}'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Update failed: {str(e)}'
        }), 500 
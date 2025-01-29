"""
System routes for version management and updates
"""
import os
import subprocess
import signal
from flask import Blueprint, jsonify, current_app
from datetime import datetime

system_bp = Blueprint('system', __name__)

def get_git_info():
    """Get current git commit information"""
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Check if .git directory exists
        if not os.path.exists(os.path.join(base_dir, '.git')):
            # Initialize git repository if it doesn't exist
            subprocess.run(['git', 'init'], cwd=base_dir, check=True)
            subprocess.run(['git', 'add', '.'], cwd=base_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=base_dir, check=True)
            current_app.logger.info("Initialized new git repository")
        
        # Get current commit hash
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=base_dir
        ).decode().strip()
        
        # Get commit date
        commit_date = subprocess.check_output(
            ['git', 'show', '-s', '--format=%ci', commit_hash],
            cwd=base_dir
        ).decode().strip()
        
        # Get branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=base_dir
        ).decode().strip()
        
        return {
            'commit_hash': commit_hash,
            'commit_date': commit_date,
            'branch': branch
        }
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Git command failed: {str(e)}")
        if e.output:
            current_app.logger.error(f"Command output: {e.output.decode()}")
        return {
            'commit_hash': 'uninitialized',
            'commit_date': datetime.now().isoformat(),
            'branch': 'main'
        }
    except Exception as e:
        current_app.logger.error(f"Error getting git info: {str(e)}")
        return {
            'commit_hash': 'error',
            'commit_date': datetime.now().isoformat(),
            'branch': 'unknown'
        }

def check_remote_updates():
    """Check for updates in the remote repository"""
    try:
        # Fetch latest changes
        subprocess.run(
            ['git', 'fetch', 'origin', 'AIgen2'],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            check=True
        )
        
        # Get number of commits behind
        result = subprocess.check_output(
            ['git', 'rev-list', 'HEAD..origin/AIgen2', '--count'],
            cwd=os.path.dirname(os.path.dirname(__file__))
        ).decode().strip()
        
        commits_behind = int(result)
        
        if commits_behind > 0:
            # Get changelog
            changes = subprocess.check_output(
                ['git', 'log', '--pretty=format:%s', 'HEAD..origin/AIgen2'],
                cwd=os.path.dirname(os.path.dirname(__file__))
            ).decode().strip().split('\n')
            
            return True, changes
        return False, []
        
    except Exception as e:
        raise RuntimeError(f"Error checking for updates: {str(e)}")

@system_bp.route('/api/v1/system/version')
def get_version():
    """Get current system version"""
    return jsonify(get_git_info())

@system_bp.route('/api/v1/system/check-update')
def check_update():
    """Check for system updates"""
    try:
        update_available, changes = check_remote_updates()
        return jsonify({
            'update_available': update_available,
            'changes': changes
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@system_bp.route('/api/v1/system/update', methods=['POST'])
def apply_update():
    """Apply system update"""
    try:
        # Pull latest changes
        subprocess.run(
            ['git', 'pull', 'origin', 'AIgen2'],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            check=True
        )
        
        # Install any new dependencies
        subprocess.run(
            ['pip', 'install', '-r', 'requirements.txt'],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            check=True
        )
        
        # Restart the service
        subprocess.run(
            ['sudo', 'systemctl', 'restart', 'birdbox'],
            check=True
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Update applied successfully'
        })
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            'status': 'error',
            'message': f'Update failed: {e.output.decode() if e.output else str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Update failed: {str(e)}'
        }), 500

@system_bp.route('/api/v1/system/reload', methods=['POST'])
def reload_server():
    """Reload the server to apply configuration changes"""
    try:
        # Get current process ID
        pid = os.getpid()
        
        # Schedule a restart after sending response
        def restart_server():
            os.kill(pid, signal.SIGTERM)
        
        current_app.logger.info("Server reload scheduled")
        
        # Schedule the restart
        from threading import Timer
        Timer(1.0, restart_server).start()
        
        return jsonify({
            'status': 'success',
            'message': 'Server reload initiated'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 
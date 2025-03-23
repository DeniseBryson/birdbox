from flask import Blueprint, jsonify, request
from features.storage import StorageManager
import shutil
import os

api_bp = Blueprint('api', __name__)

# System endpoints
@api_bp.route('/system/status', methods=['GET'])
def system_status():
    """Get system status"""
    return jsonify({"status": "operational"})

@api_bp.route('/system/health', methods=['GET'])
def system_health():
    """Get system health metrics"""
    return jsonify({"health": "good"})

# Camera endpoints
@api_bp.route('/camera/stream', methods=['GET'])
def camera_stream():
    """Get camera stream"""
    return jsonify({"stream_url": "/ws/camera-feed"})

@api_bp.route('/camera/record/start', methods=['POST'])
def start_recording():
    """Start camera recording"""
    return jsonify({"status": "recording started"})

# Hardware endpoints
@api_bp.route('/hardware/gpio/status', methods=['GET'])
def gpio_status():
    """Get GPIO status"""
    return jsonify({"gpio": "operational"})

@api_bp.route('/hardware/motors/status', methods=['GET'])
def motor_status():
    """Get motor status"""
    return jsonify({"motors": "operational"})

# Configuration endpoints
@api_bp.route('/config/profiles', methods=['GET'])
def get_profiles():
    """Get configuration profiles"""
    return jsonify({"profiles": []})

@api_bp.route('/config/settings', methods=['GET'])
def get_settings():
    """Get system settings"""
    return jsonify({"settings": {}})

@api_bp.route('/config/storage', methods=['GET'])
def get_storage_config():
    """Get storage configuration and disk information"""
    try:
        storage_manager = StorageManager('storage')
        stats = storage_manager.get_statistics()
        
        # Get actual disk information
        total, used, free = shutil.disk_usage(str(storage_manager.storage_path))
        
        return jsonify({
            "storage_limit": storage_manager.storage_limit,
            "warning_threshold": storage_manager.warning_threshold,
            "retention_days": storage_manager.retention_days,
            "disk_total": total,
            "disk_used": used,
            "disk_free": free
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/config/storage', methods=['POST'])
def update_storage_config():
    """Update storage configuration"""
    try:
        data = request.get_json()
        
        # Validate input
        if not all(k in data for k in ['storage_limit', 'warning_threshold', 'retention_days']):
            return jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400
            
        # Get disk information to validate storage limit
        total, _, _ = shutil.disk_usage('storage')
        if data['storage_limit'] > total:
            return jsonify({
                "status": "error",
                "message": "Storage limit cannot exceed total disk space"
            }), 400
            
        if data['warning_threshold'] < 0.5 or data['warning_threshold'] > 0.95:
            return jsonify({
                "status": "error",
                "message": "Warning threshold must be between 50% and 95%"
            }), 400
            
        if data['retention_days'] < 1 or data['retention_days'] > 365:
            return jsonify({
                "status": "error",
                "message": "Retention period must be between 1 and 365 days"
            }), 400
        
        # Update configuration
        storage_manager = StorageManager('storage')
        if not storage_manager.update_config(
            storage_limit=data['storage_limit'],
            warning_threshold=data['warning_threshold'],
            retention_days=data['retention_days']
        ):
            return jsonify({
                "status": "error",
                "message": "Failed to save configuration"
            }), 500
            
        # Save the configuration to .env file
        if not storage_manager.save_config():
            return jsonify({
                "status": "error",
                "message": "Failed to persist configuration"
            }), 500
            
        return jsonify({
            "status": "success",
            "message": "Storage configuration updated"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Maintenance endpoints
@api_bp.route('/maintenance/food-level', methods=['GET'])
def food_level():
    """Get food level"""
    return jsonify({"food_level": "unknown"})

@api_bp.route('/maintenance/storage/status', methods=['GET'])
def storage_status():
    """Get storage status"""
    try:
        storage_manager = StorageManager('storage')  # Use default storage path
        stats = storage_manager.get_statistics()
        video_files = storage_manager.get_video_files()
        
        return jsonify({
            "storage": {
                "storage_status": stats["storage_status"],
                "total_videos": stats["total_videos"],
                "total_size": stats["total_size"],
                "oldest_file": stats["oldest_file"].isoformat() if stats["oldest_file"] else None,
                "newest_file": stats["newest_file"].isoformat() if stats["newest_file"] else None,
                "retention_days": stats["retention_days"],
                "warning_threshold": stats["warning_threshold"],
                "video_files": video_files
            }
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "storage": {
                "storage_status": {
                    "total": 0,
                    "used": 0,
                    "free": 0,
                    "warning": False
                },
                "total_videos": 0,
                "total_size": 0,
                "video_files": []
            }
        }), 500

# Analytics endpoints
@api_bp.route('/analytics/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    return jsonify({"statistics": {}}) 
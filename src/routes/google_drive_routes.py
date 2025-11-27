from flask import Blueprint, jsonify
from ..services.google_drive_service import google_drive_service

google_drive_bp = Blueprint('google_drive', __name__, url_prefix='/api/google-drive')

@google_drive_bp.route('/status', methods=['GET'])
def google_drive_status():
    """Devuelve el estado del token y configuración"""
    status = google_drive_service.get_token_status()
    return jsonify({
        'success': True,
        'data': status
    })

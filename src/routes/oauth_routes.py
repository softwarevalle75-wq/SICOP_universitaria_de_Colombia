from flask import Blueprint, request, jsonify, redirect, url_for
from ..services.google_drive_service import google_drive_service

oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')

@oauth_bp.route('/google/status', methods=['GET'])
def google_status():
    """Verifica el estado de la autenticación con Google Drive"""
    status = google_drive_service.get_token_status()
    return jsonify({
        'success': True,
        'data': status
    })

@oauth_bp.route('/google/authorize', methods=['GET'])
def google_authorize():
    """Inicia el flujo de autorización OAuth con Google"""
    #redirect_uri = request.host_url.rstrip('/') + '/oauth/google/callback'
    redirect_uri = "http://localhost:5000/oauth/google/callback"


    auth_url = google_drive_service.get_auth_url(redirect_uri)

    if not auth_url:
        return jsonify({
            'error': 'No se pudo generar URL de autorización. Verifica GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en .env',
            'codigo': 'OAUTH_CONFIG_ERROR'
        }), 500

    return redirect(auth_url)

@oauth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """Callback de OAuth después de la autorización"""
    error = request.args.get('error')
    if error:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1 style="color: #dc3545;">Error de Autorización</h1>
            <p>Google rechazó la autorización: {error}</p>
            <a href="/" style="color: #007bff;">Volver al inicio</a>
        </body>
        </html>
        """, 400

    #redirect_uri = request.host_url.rstrip('/') + '/oauth/google/callback'
    redirect_uri = "http://localhost:5000/oauth/google/callback"
    authorization_response = request.url

    """if authorization_response.startswith('http://') and 'localhost' not in authorization_response:
        authorization_response = authorization_response.replace('http://', 'https://', 1)"""
    
    authorization_response = authorization_response.replace("127.0.0.1", "localhost")
    redirect_uri = "http://localhost:5000/oauth/google/callback"


    success = google_drive_service.handle_oauth_callback(authorization_response, redirect_uri)

    if success:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1 style="color: #28a745;">Autorización Exitosa</h1>
            <p>Google Drive ha sido conectado correctamente.</p>
            <p>Ya puedes subir archivos PDF.</p>
            <a href="/" style="color: #007bff; text-decoration: none; padding: 10px 20px; background: #007bff; color: white; border-radius: 5px;">Volver al inicio</a>
        </body>
        </html>
        """
    else:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h1 style="color: #dc3545;">Error al Guardar Token</h1>
            <p>No se pudo completar la autorización. Intenta de nuevo.</p>
            <a href="/oauth/google/authorize" style="color: #007bff;">Reintentar</a>
        </body>
        </html>
        """, 500

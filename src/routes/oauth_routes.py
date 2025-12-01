from flask import Blueprint, request, jsonify, redirect
from ..services.google_drive_service import google_drive_service

oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')


@oauth_bp.route('/google/status', methods=['GET'])
def google_status():
    status = google_drive_service.get_token_status()
    return jsonify({'success': True, 'data': status})


@oauth_bp.route('/google/authorize', methods=['GET'])
def google_authorize():
    """Inicia OAuth dinámicamente según el dominio (local o Railway)."""

    # Construye la URL correcta según el dominio
    redirect_uri = request.host_url.rstrip('/') + '/oauth/google/callback'

    # 🔥 FORZAR HTTPS EN RAILWAY (muy importante)
    if "railway.app" in redirect_uri:
        redirect_uri = redirect_uri.replace("http://", "https://")

    print("REDIRECT URI USADA:", redirect_uri)

    auth_url = google_drive_service.get_auth_url(redirect_uri)

    if not auth_url:
        return jsonify({
            'error': 'No se pudo generar URL de autorización',
            'codigo': 'OAUTH_CONFIG_ERROR'
        }), 500

    return redirect(auth_url)
    #Pruebas

@oauth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """Callback desde Google OAuth"""

    error = request.args.get('error')
    if error:
        return f"<h1>Error: {error}</h1>", 400

    # Reconstruimos el redirect_uri
    redirect_uri = request.host_url.rstrip('/') + '/oauth/google/callback'

    # 🔥 FORZAR HTTPS EN RAILWAY TAMBIÉN AQUÍ
    if "railway.app" in redirect_uri:
        redirect_uri = redirect_uri.replace("http://", "https://")

    authorization_response = request.url

    # Corrige si Google responde con http
    if "railway.app" in authorization_response:
        authorization_response = authorization_response.replace("http://", "https://")

    print("CALLBACK REDIRECT URI:", redirect_uri)
    print("CALLBACK AUTH RESPONSE:", authorization_response)

    success = google_drive_service.handle_oauth_callback(
        authorization_response,
        redirect_uri
    )
    #Pruebas
    if success:
        return """
        <h1>Autorización exitosa</h1>
        <p>Google Drive está conectado.</p>
        <a href="/">Volver</a>
        """

    return """
    <h1>Error guardando token</h1>
    <a href="/oauth/google/authorize">Reintentar</a>
    """, 500

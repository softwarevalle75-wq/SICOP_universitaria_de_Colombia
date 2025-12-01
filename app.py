from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import sys
from datetime import datetime
import traceback  # <-- Necesario para debug avanzado

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Importar configuracion
from src.config.settings import Config

# Importar blueprints
from src.routes.pdf_reception_routes import pdf_reception_bp
from src.routes.chat_routes import chat_bp
from src.routes.auth_routes import auth_bp
from src.routes.oauth_routes import oauth_bp
from src.routes.google_drive_routes import google_drive_bp

# Importar autenticacion
from src.services.auth_service import (
    auth_service, get_token_from_request, token_required
)

# Importar base de datos de usuarios
from src.database.user_models import user_db_manager


def create_app():
    """Factory function para crear la aplicacion Flask"""
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    # Configurar la aplicacion
    app.config.update({
        'MAX_CONTENT_LENGTH': Config.MAX_FILE_SIZE,
        'SECRET_KEY': Config.SECRET_KEY or 'dev-secret-key-change-in-production',
    })

    # Inicializar base de datos de usuarios
    try:
        user_db_manager.init_database()
        print("Base de datos de usuarios inicializada correctamente")
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")

    # Crear directorios necesarios
    Config.create_directories()

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(pdf_reception_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(google_drive_bp)

    # Ruta principal
    @app.route('/')
    def index():
        token = get_token_from_request()

        if not token:
            return redirect(url_for('auth.login_page'))

        payload = auth_service.verify_access_token(token)

        if not payload:
            return redirect(url_for('auth.login_page'))

        user = {
            'id': payload['user_id'],
            'email': payload['email'],
            'rol': payload['rol']
        }

        return render_template('Index.html', user=user)

    @app.route('/health')
    def health_check():
        try:
            db_status = user_db_manager.test_connection()
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected' if db_status else 'disconnected',
                'version': '2.0.0'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500

    @app.route('/api/info')
    def api_info():
        return jsonify({
            'name': 'Sistema de Procesamiento de PDFs',
            'version': '2.0.0',
            'description': 'API para recepcion y procesamiento de documentos PDF',
            'endpoints': {
                'pdf_upload': '/pdf/upload',
                'pdf_status': '/pdf/status/<document_id>',
                'pdf_list': '/pdf/list',
                'pdf_stats': '/pdf/stats',
                'chat_message': '/chat/message',
                'chat_history': '/chat/history',
                'chat_search': '/chat/search',
                'auth_login': '/auth/login',
                'auth_registro': '/auth/registro',
                'oauth_status': '/oauth/google/status',
                'oauth_authorize': '/oauth/google/authorize',
                'health': '/health'
            },
            'max_file_size': Config.MAX_FILE_SIZE
        })

    # -------------------------
    # MANEJO DE ERRORES
    # -------------------------

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint no encontrado',
            'code': 'NOT_FOUND',
            'timestamp': datetime.now().isoformat()
        }), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({
            'error': f'Archivo demasiado grande. Máximo permitido: {Config.MAX_FILE_SIZE // (1024*1024)}MB',
            'code': 'FILE_TOO_LARGE',
            'timestamp': datetime.now().isoformat()
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Error interno del servidor',
            'code': 'INTERNAL_ERROR',
            'timestamp': datetime.now().isoformat()
        }), 500

    # -------------------------
    # 🔥 CAPTURA GLOBAL DE ERRORES 500
    # -------------------------

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        print("\n\n🔥🔥🔥 ERROR NO CAPTURADO 🔥🔥🔥")
        traceback.print_exc()  # Manda stacktrace a Railway Logs

        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

    # -------------------------
    # REQUEST LOGGING & CORS
    # -------------------------

    @app.before_request
    def log_request_info():
        if not request.path.startswith('/static'):
            print(f"[{datetime.now()}] {request.method} {request.path} - {request.remote_addr}")

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        response.headers['Access-Control-Allow-Origin'] = origin or '*'
        response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @app.route('/api/<path:any_path>', methods=['OPTIONS'])
    def cors_preflight(any_path):
        return ('', 204)

    return app


# Crear instancia de la aplicacion
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    print(f"Iniciando servidor en puerto {port}...")
    print(f"Modo debug: {debug}")
    print(f"Directorio de trabajo: {os.getcwd()}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )

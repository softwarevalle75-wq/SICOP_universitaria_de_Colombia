from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response
from datetime import datetime

from ..services.auth_service import (
    auth_service, token_required, admin_required,
    set_auth_cookies, clear_auth_cookies, get_token_from_request
)
from ..database.user_models import UserRole, usuario_model

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ==================== PAGINAS ====================

@auth_bp.route('/login')
def login_page():
    """Pagina de login"""
    # Si ya esta autenticado, redirigir a home
    token = get_token_from_request()
    if token and auth_service.verify_access_token(token):
        return redirect(url_for('index'))
    return render_template('login.html')


@auth_bp.route('/registro')
def registro_page():
    """Pagina de registro"""
    # Si ya esta autenticado, redirigir a home
    token = get_token_from_request()
    if token and auth_service.verify_access_token(token):
        return redirect(url_for('index'))
    return render_template('registro.html')


# ==================== API ENDPOINTS ====================

@auth_bp.route('/api/registro', methods=['POST'])
def api_registro():
    """Endpoint para registrar un nuevo usuario"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400

        # Validar campos requeridos
        required_fields = ['email', 'password', 'nombre', 'apellido']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Campo {field} es requerido'}), 400

        # Registrar usuario (rol por defecto: usuario)
        result = auth_service.registrar_usuario(
            email=data['email'],
            password=data['password'],
            nombre=data['nombre'],
            apellido=data['apellido'],
            rol=UserRole.USUARIO
        )

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """Endpoint para iniciar sesion"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Email y password son requeridos'}), 400

        result = auth_service.login(email, password)

        if result['success']:
            # Crear respuesta con cookies
            response = make_response(jsonify(result))
            response = set_auth_cookies(
                response,
                result['access_token'],
                result['refresh_token']
            )
            return response
        else:
            return jsonify(result), 401

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Endpoint para refrescar el access token"""
    try:
        # Obtener refresh token de cookie o body
        refresh_token = request.cookies.get('refresh_token')
        if not refresh_token:
            data = request.get_json() or {}
            refresh_token = data.get('refresh_token')

        if not refresh_token:
            return jsonify({'success': False, 'error': 'Refresh token requerido'}), 400

        result = auth_service.refresh_access_token(refresh_token)

        if result['success']:
            response = make_response(jsonify(result))
            # Actualizar cookie del access token
            response.set_cookie(
                'access_token',
                result['access_token'],
                httponly=True,
                secure=not auth_service.jwt_secret.startswith('dev'),
                samesite='Lax',
                max_age=auth_service.access_token_expires
            )
            return response
        else:
            return jsonify(result), 401

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """Endpoint para cerrar sesion"""
    try:
        refresh_token = request.cookies.get('refresh_token')
        if refresh_token:
            auth_service.logout(refresh_token)

        response = make_response(jsonify({'success': True, 'message': 'Sesion cerrada'}))
        response = clear_auth_cookies(response)
        return response

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/me', methods=['GET'])
@token_required
def api_me():
    """Obtiene informacion del usuario actual"""
    try:
        user = usuario_model.obtener_por_id(request.current_user['id'])
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'nombre': user['nombre'],
                    'apellido': user['apellido'],
                    'rol': user['rol'],
                    'fecha_creacion': user['fecha_creacion'].isoformat() if user['fecha_creacion'] else None,
                    'ultimo_login': user['ultimo_login'].isoformat() if user['ultimo_login'] else None
                }
            })
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/verificar', methods=['GET'])
def api_verificar():
    """Verifica si el usuario esta autenticado"""
    token = get_token_from_request()
    if not token:
        return jsonify({'authenticated': False}), 200

    payload = auth_service.verify_access_token(token)
    if payload:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': payload['user_id'],
                'email': payload['email'],
                'rol': payload['rol']
            }
        })
    return jsonify({'authenticated': False}), 200


# ==================== ADMIN ENDPOINTS ====================

@auth_bp.route('/api/usuarios', methods=['GET'])
@admin_required
def api_listar_usuarios():
    """Lista todos los usuarios (solo admin)"""
    try:
        limite = request.args.get('limite', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        usuarios = usuario_model.listar_todos(limite, offset)

        # Convertir fechas a string
        for u in usuarios:
            if u.get('fecha_creacion'):
                u['fecha_creacion'] = u['fecha_creacion'].isoformat()
            if u.get('ultimo_login'):
                u['ultimo_login'] = u['ultimo_login'].isoformat()

        return jsonify({'success': True, 'usuarios': usuarios})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/usuarios/<int:user_id>/rol', methods=['PUT'])
@admin_required
def api_cambiar_rol(user_id):
    """Cambia el rol de un usuario (solo admin)"""
    try:
        data = request.get_json()
        nuevo_rol = data.get('rol')

        if nuevo_rol not in ['administrador', 'profesor', 'usuario']:
            return jsonify({'success': False, 'error': 'Rol invalido'}), 400

        # No permitir cambiar el propio rol
        if user_id == request.current_user['id']:
            return jsonify({'success': False, 'error': 'No puedes cambiar tu propio rol'}), 400

        rol_enum = UserRole(nuevo_rol)
        if usuario_model.cambiar_rol(user_id, rol_enum):
            return jsonify({'success': True, 'message': 'Rol actualizado'})
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/usuarios/<int:user_id>/desactivar', methods=['POST'])
@admin_required
def api_desactivar_usuario(user_id):
    """Desactiva un usuario (solo admin)"""
    try:
        # No permitir desactivarse a si mismo
        if user_id == request.current_user['id']:
            return jsonify({'success': False, 'error': 'No puedes desactivarte a ti mismo'}), 400

        if usuario_model.desactivar(user_id):
            return jsonify({'success': True, 'message': 'Usuario desactivado'})
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/usuarios/<int:user_id>/activar', methods=['POST'])
@admin_required
def api_activar_usuario(user_id):
    """Activa un usuario (solo admin)"""
    try:
        if usuario_model.activar(user_id):
            return jsonify({'success': True, 'message': 'Usuario activado'})
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/registro-admin', methods=['POST'])
@admin_required
def api_registro_admin():
    """Registra un usuario con rol especifico (solo admin)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'Datos no proporcionados'}), 400

        required_fields = ['email', 'password', 'nombre', 'apellido', 'rol']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Campo {field} es requerido'}), 400

        if data['rol'] not in ['administrador', 'profesor', 'usuario']:
            return jsonify({'success': False, 'error': 'Rol invalido'}), 400

        result = auth_service.registrar_usuario(
            email=data['email'],
            password=data['password'],
            nombre=data['nombre'],
            apellido=data['apellido'],
            rol=UserRole(data['rol'])
        )

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

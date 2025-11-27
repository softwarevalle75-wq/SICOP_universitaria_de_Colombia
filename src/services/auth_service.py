import bcrypt
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
from functools import wraps
from flask import request, jsonify, make_response

from ..config.settings import Config
from ..database.user_models import (
    usuario_model, refresh_token_model, user_db_manager,
    UserRole
)


class AuthService:
    """Servicio de autenticacion con bcrypt y JWT"""

    def __init__(self):
        self.jwt_secret = Config.JWT_SECRET_KEY
        self.access_token_expires = Config.JWT_ACCESS_TOKEN_EXPIRES
        self.refresh_token_expires = Config.JWT_REFRESH_TOKEN_EXPIRES

    # ==================== PASSWORD HASHING ====================

    def hash_password(self, password: str) -> str:
        """Hashea una contraseña con bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica una contraseña contra su hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False

    # ==================== JWT TOKENS ====================

    def generate_access_token(self, user_id: int, email: str, rol: str) -> str:
        """Genera un access token JWT"""
        payload = {
            'user_id': user_id,
            'email': email,
            'rol': rol,
            'type': 'access',
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(seconds=self.access_token_expires)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    def generate_refresh_token(self, user_id: int) -> Tuple[str, str]:
        """Genera un refresh token y su hash para almacenar"""
        token = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(seconds=self.refresh_token_expires)

        # Guardar en base de datos
        refresh_token_model.guardar(user_id, token_hash, expires_at)

        return token, token_hash

    def verify_access_token(self, token: str) -> Optional[Dict]:
        """Verifica y decodifica un access token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            if payload.get('type') != 'access':
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_refresh_token(self, token: str) -> Optional[Dict]:
        """Verifica un refresh token"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return refresh_token_model.verificar(token_hash)

    def revoke_refresh_token(self, token: str) -> bool:
        """Revoca un refresh token"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return refresh_token_model.revocar(token_hash)

    # ==================== REGISTRO Y LOGIN ====================

    def registrar_usuario(self, email: str, password: str, nombre: str,
                            apellido: str, rol: UserRole = UserRole.USUARIO) -> Dict:
        """Registra un nuevo usuario"""
        # Validar email
        if not email or '@' not in email:
            return {'success': False, 'error': 'Email invalido'}

        # Validar password
        if len(password) < 8:
            return {'success': False, 'error': 'La contraseña debe tener al menos 8 caracteres'}

        # Verificar si email existe
        if usuario_model.email_existe(email):
            return {'success': False, 'error': 'El email ya esta registrado'}

        # Hashear password
        password_hash = self.hash_password(password)

        # Crear usuario
        user_id = usuario_model.crear(email, password_hash, nombre, apellido, rol)

        if user_id:
            return {
                'success': True,
                'user_id': user_id,
                'message': 'Usuario registrado exitosamente'
            }
        else:
            return {'success': False, 'error': 'Error al crear el usuario'}

    def login(self, email: str, password: str) -> Dict:
        """Autentica un usuario y genera tokens"""
        # Obtener usuario
        user = usuario_model.obtener_por_email(email)

        if not user:
            return {'success': False, 'error': 'Credenciales invalidas'}

        # Verificar si esta activo
        if not user['activo']:
            return {'success': False, 'error': 'Cuenta desactivada'}

        # Verificar password
        if not self.verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Credenciales invalidas'}

        # Actualizar ultimo login
        usuario_model.actualizar_ultimo_login(user['id'])

        # Generar tokens
        access_token = self.generate_access_token(user['id'], user['email'], user['rol'])
        refresh_token, _ = self.generate_refresh_token(user['id'])

        return {
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'nombre': user['nombre'],
                'apellido': user['apellido'],
                'rol': user['rol']
            }
        }

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """Genera un nuevo access token usando el refresh token"""
        # Verificar refresh token
        token_data = self.verify_refresh_token(refresh_token)

        if not token_data:
            return {'success': False, 'error': 'Refresh token invalido o expirado'}

        # Generar nuevo access token
        access_token = self.generate_access_token(
            token_data['user_id'],
            token_data['email'],
            token_data['rol']
        )

        return {
            'success': True,
            'access_token': access_token
        }

    def logout(self, refresh_token: str) -> Dict:
        """Cierra la sesion revocando el refresh token"""
        if self.revoke_refresh_token(refresh_token):
            return {'success': True, 'message': 'Sesion cerrada exitosamente'}
        return {'success': False, 'error': 'Error al cerrar sesion'}

    def logout_all_devices(self, user_id: int) -> Dict:
        """Cierra todas las sesiones de un usuario"""
        if refresh_token_model.revocar_todos_usuario(user_id):
            return {'success': True, 'message': 'Todas las sesiones cerradas'}
        return {'success': False, 'error': 'Error al cerrar sesiones'}


# Instancia global
auth_service = AuthService()


# ==================== DECORADORES Y MIDDLEWARE ====================

def get_token_from_request() -> Optional[str]:
    """Obtiene el token de la cookie o del header Authorization"""
    # Primero intentar desde cookie
    token = request.cookies.get('access_token')
    if token:
        return token

    # Si no hay cookie, buscar en header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]

    return None


def token_required(f):
    """Decorador que requiere autenticacion"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()

        if not token:
            return jsonify({'error': 'Token de acceso requerido'}), 401

        payload = auth_service.verify_access_token(token)

        if not payload:
            return jsonify({'error': 'Token invalido o expirado'}), 401

        # Agregar info del usuario al request
        request.current_user = {
            'id': payload['user_id'],
            'email': payload['email'],
            'rol': payload['rol']
        }

        return f(*args, **kwargs)

    return decorated


def roles_required(*roles):
    """Decorador que requiere roles especificos"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_request()

            if not token:
                return jsonify({'error': 'Token de acceso requerido'}), 401

            payload = auth_service.verify_access_token(token)

            if not payload:
                return jsonify({'error': 'Token invalido o expirado'}), 401

            # Verificar rol
            user_role = payload.get('rol')
            if user_role not in roles:
                return jsonify({'error': 'No tienes permisos para esta accion'}), 403

            request.current_user = {
                'id': payload['user_id'],
                'email': payload['email'],
                'rol': payload['rol']
            }

            return f(*args, **kwargs)

        return decorated
    return decorator


def admin_required(f):
    """Decorador que requiere rol de administrador"""
    return roles_required('administrador')(f)


def profesor_required(f):
    """Decorador que requiere rol de profesor o superior"""
    return roles_required('administrador', 'profesor')(f)


def set_auth_cookies(response, access_token: str, refresh_token: str):
    """Configura las cookies de autenticacion"""
    # Access token cookie (httponly, secure en produccion)
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=not Config.DEBUG,  # Solo HTTPS en produccion
        samesite='Lax',
        max_age=Config.JWT_ACCESS_TOKEN_EXPIRES
    )

    # Refresh token cookie
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,
        secure=not Config.DEBUG,
        samesite='Lax',
        max_age=Config.JWT_REFRESH_TOKEN_EXPIRES,
        path='/auth'  # Solo accesible desde rutas /auth
    )

    return response


def clear_auth_cookies(response):
    """Elimina las cookies de autenticacion"""
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token', path='/auth')
    return response

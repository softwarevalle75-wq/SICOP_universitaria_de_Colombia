import mysql.connector
from mysql.connector import Error
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
from ..config.settings import Config


class UserRole(Enum):
    """Roles de usuario disponibles"""
    ADMIN = 'administrador'
    PROFESOR = 'profesor'
    USUARIO = 'usuario'


class MySQLUserManager:
    """Gestor de usuarios en MySQL"""

    def __init__(self):
        self.config = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
        }
        self.database = Config.MYSQL_DATABASE

    def get_connection(self, with_database: bool = True):
        """Obtiene una conexion a MySQL"""
        try:
            config = self.config.copy()
            if with_database:
                config['database'] = self.database
            conn = mysql.connector.connect(**config)
            return conn
        except Error as e:
            print(f"Error conectando a MySQL: {e}")
            raise

    def init_database(self):
        """Inicializa la base de datos y tablas de usuarios"""
        try:
            # Crear base de datos si no existe
            conn = self.get_connection(with_database=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            cursor.close()
            conn.close()

            # Crear tablas
            conn = self.get_connection()
            cursor = conn.cursor()

            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    nombre VARCHAR(100) NOT NULL,
                    apellido VARCHAR(100) NOT NULL,
                    rol ENUM('administrador', 'profesor', 'usuario') NOT NULL DEFAULT 'usuario',
                    activo BOOLEAN DEFAULT TRUE,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    ultimo_login TIMESTAMP NULL,
                    INDEX idx_email (email),
                    INDEX idx_rol (rol),
                    INDEX idx_activo (activo)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            # Tabla de tokens de refresco (para invalidar sesiones)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token_hash VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revoked BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                    INDEX idx_token_hash (token_hash),
                    INDEX idx_user_id (user_id),
                    INDEX idx_expires (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')

            conn.commit()
            cursor.close()
            conn.close()
            print("Base de datos de usuarios inicializada correctamente")
            return True

        except Error as e:
            print(f"Error inicializando base de datos de usuarios: {e}")
            return False

    def test_connection(self) -> bool:
        """Prueba la conexion a la base de datos"""
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except:
            return False


class Usuario:
    """Modelo para gestionar usuarios"""

    def __init__(self, db_manager: MySQLUserManager):
        self.db = db_manager

    def crear(self, email: str, password_hash: str, nombre: str, apellido: str,
              rol: UserRole = UserRole.USUARIO) -> Optional[int]:
        """Crea un nuevo usuario"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usuarios (email, password_hash, nombre, apellido, rol)
                VALUES (%s, %s, %s, %s, %s)
            ''', (email.lower(), password_hash, nombre, apellido, rol.value))
            user_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            return user_id
        except Error as e:
            print(f"Error creando usuario: {e}")
            return None

    def obtener_por_email(self, email: str) -> Optional[Dict]:
        """Obtiene un usuario por su email"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM usuarios WHERE email = %s', (email.lower(),))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Error as e:
            print(f"Error obteniendo usuario: {e}")
            return None

    def obtener_por_id(self, user_id: int) -> Optional[Dict]:
        """Obtiene un usuario por su ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM usuarios WHERE id = %s', (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Error as e:
            print(f"Error obteniendo usuario: {e}")
            return None

    def actualizar_ultimo_login(self, user_id: int) -> bool:
        """Actualiza la fecha del ultimo login"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = %s
            ''', (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"Error actualizando ultimo login: {e}")
            return False

    def email_existe(self, email: str) -> bool:
        """Verifica si un email ya esta registrado"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM usuarios WHERE email = %s', (email.lower(),))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count > 0
        except Error as e:
            print(f"Error verificando email: {e}")
            return True  # Por seguridad, asumir que existe

    def listar_todos(self, limite: int = 50, offset: int = 0) -> List[Dict]:
        """Lista todos los usuarios"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT id, email, nombre, apellido, rol, activo, fecha_creacion, ultimo_login
                FROM usuarios
                ORDER BY fecha_creacion DESC
                LIMIT %s OFFSET %s
            ''', (limite, offset))
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return users
        except Error as e:
            print(f"Error listando usuarios: {e}")
            return []

    def cambiar_rol(self, user_id: int, nuevo_rol: UserRole) -> bool:
        """Cambia el rol de un usuario"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE usuarios SET rol = %s WHERE id = %s
            ''', (nuevo_rol.value, user_id))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except Error as e:
            print(f"Error cambiando rol: {e}")
            return False

    def desactivar(self, user_id: int) -> bool:
        """Desactiva un usuario"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE usuarios SET activo = FALSE WHERE id = %s', (user_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except Error as e:
            print(f"Error desactivando usuario: {e}")
            return False

    def activar(self, user_id: int) -> bool:
        """Activa un usuario"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE usuarios SET activo = TRUE WHERE id = %s', (user_id,))
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            return affected > 0
        except Error as e:
            print(f"Error activando usuario: {e}")
            return False


class RefreshToken:
    """Modelo para gestionar tokens de refresco"""

    def __init__(self, db_manager: MySQLUserManager):
        self.db = db_manager

    def guardar(self, user_id: int, token_hash: str, expires_at: datetime) -> bool:
        """Guarda un nuevo refresh token"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
            ''', (user_id, token_hash, expires_at))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"Error guardando refresh token: {e}")
            return False

    def verificar(self, token_hash: str) -> Optional[Dict]:
        """Verifica si un refresh token es valido"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('''
                SELECT rt.*, u.email, u.rol, u.activo
                FROM refresh_tokens rt
                JOIN usuarios u ON rt.user_id = u.id
                WHERE rt.token_hash = %s
                AND rt.revoked = FALSE
                AND rt.expires_at > NOW()
                AND u.activo = TRUE
            ''', (token_hash,))
            token = cursor.fetchone()
            cursor.close()
            conn.close()
            return token
        except Error as e:
            print(f"Error verificando refresh token: {e}")
            return None

    def revocar(self, token_hash: str) -> bool:
        """Revoca un refresh token"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE refresh_tokens SET revoked = TRUE WHERE token_hash = %s', (token_hash,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"Error revocando refresh token: {e}")
            return False

    def revocar_todos_usuario(self, user_id: int) -> bool:
        """Revoca todos los tokens de un usuario"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = %s', (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            print(f"Error revocando tokens: {e}")
            return False

    def limpiar_expirados(self) -> int:
        """Elimina tokens expirados"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM refresh_tokens WHERE expires_at < NOW() OR revoked = TRUE')
            conn.commit()
            deleted = cursor.rowcount
            cursor.close()
            conn.close()
            return deleted
        except Error as e:
            print(f"Error limpiando tokens: {e}")
            return 0


# Instancias globales
user_db_manager = MySQLUserManager()
usuario_model = Usuario(user_db_manager)
refresh_token_model = RefreshToken(user_db_manager)

import pymysql
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List


class DatabaseManager:
    """Gestor de base de datos MySQL"""

    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.database = os.getenv("MYSQL_DATABASE", "sgdea_users")
        self.port = int(os.getenv("MYSQL_PORT", "3306"))

        self.init_database()

    def get_connection(self):
        """Obtiene una conexión MySQL"""
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def init_database(self):
        """Inicializa tablas sin recrear índices (para evitar errores en MySQL)."""

        conn = self.get_connection()
        cursor = conn.cursor()

        # --- TABLAS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos_recibidos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre_pdf VARCHAR(255) NOT NULL,
                url_google_drive TEXT NOT NULL,
                fecha_hora_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dominio_origen VARCHAR(255) NOT NULL,
                estado_procesamiento VARCHAR(50) DEFAULT 'pendiente',
                tamano_archivo BIGINT,
                hash_archivo VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos_procesados (
                id INT AUTO_INCREMENT PRIMARY KEY,
                documento_id INT NOT NULL,
                contenido_json JSON NOT NULL,
                fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version_procesamiento VARCHAR(20) DEFAULT '1.0',
                tiempo_procesamiento_segundos FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (documento_id) REFERENCES documentos_recibidos(id)
                    ON DELETE CASCADE
            );
        """)

        cursor.close()
        conn.close()

    def test_connection(self) -> bool:
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except:
            return False


class DocumentoRecibido:
    """Modelo para documentos recibidos"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def crear(self, nombre_pdf, url_google_drive, dominio_origen,
              tamano_archivo=None, hash_archivo=None):

        conn = self.db.get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO documentos_recibidos 
            (nombre_pdf, url_google_drive, dominio_origen, tamano_archivo, hash_archivo)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (nombre_pdf, url_google_drive, dominio_origen,
                             tamano_archivo, hash_archivo))

        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return new_id

    def obtener_por_id(self, documento_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documentos_recibidos WHERE id=%s", (documento_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def actualizar_estado(self, documento_id, estado):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE documentos_recibidos
            SET estado_procesamiento=%s
            WHERE id=%s
        """, (estado, documento_id))
        updated = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return updated

    def listar_pendientes(self):
        conn = self.db.get_connectio_

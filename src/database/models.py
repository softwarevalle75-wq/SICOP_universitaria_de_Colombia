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
        """Inicializa tablas e índices compatibles con MySQL"""

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

        # --- ÍNDICES MYSQL (no soportan IF NOT EXISTS) ---
        indices = [
            ("idx_doc_rec_fecha", "documentos_recibidos", "fecha_hora_recepcion"),
            ("idx_doc_rec_dominio", "documentos_recibidos", "dominio_origen"),
            ("idx_doc_rec_estado", "documentos_recibidos", "estado_procesamiento"),
            ("idx_doc_proc_docid", "documentos_procesados", "documento_id")
        ]

        for index_name, table, column in indices:
            cursor.execute(f"""
                SELECT COUNT(1)
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table}'
                AND INDEX_NAME = '{index_name}';
            """)

            exists = cursor.fetchone()["COUNT(1)"]

            if exists == 0:
                cursor.execute(f"""
                    CREATE INDEX {index_name}
                    ON {table}({column});
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
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documentos_recibidos 
            WHERE estado_procesamiento='pendiente'
            ORDER BY fecha_hora_recepcion
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def listar_por_dominio(self, dominio):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documentos_recibidos 
            WHERE dominio_origen=%s
            ORDER BY fecha_hora_recepcion DESC
        """, (dominio,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def listar_todos(self, limite=50, offset=0):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documentos_recibidos
            ORDER BY fecha_hora_recepcion DESC
            LIMIT %s OFFSET %s
        """, (limite, offset))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def listar_por_estado(self, estado):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documentos_recibidos
            WHERE estado_procesamiento=%s
            ORDER BY fecha_hora_recepcion DESC
        """, (estado,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def contar_todos(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM documentos_recibidos;")
        total = cursor.fetchone()["total"]
        cursor.close()
        conn.close()
        return total

    def eliminar(self, documento_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM documentos_procesados WHERE documento_id=%s", (documento_id,))
        cursor.execute("DELETE FROM documentos_recibidos WHERE id=%s", (documento_id,))

        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return deleted


class DocumentoProcesado:
    """Modelo para documentos procesados"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def crear(self, documento_id, contenido_json,
              tiempo_procesamiento=None, version='1.0'):

        conn = self.db.get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO documentos_procesados
            (documento_id, contenido_json, version_procesamiento, tiempo_procesamiento_segundos)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(sql, (
            documento_id,
            json.dumps(contenido_json, ensure_ascii=False),
            version,
            tiempo_procesamiento
        ))

        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return new_id

    def obtener_por_documento_id(self, documento_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT dp.*, dr.nombre_pdf, dr.dominio_origen, dr.fecha_hora_recepcion
            FROM documentos_procesados dp
            JOIN documentos_recibidos dr ON dp.documento_id = dr.id
            WHERE dp.documento_id=%s
            ORDER BY dp.fecha_procesamiento DESC
            LIMIT 1
        """

        cursor.execute(sql, (documento_id,))
        row = cursor.fetchone()

        if row and "contenido_json" in row:
            row["contenido_json"] = json.loads(row["contenido_json"])

        cursor.close()
        conn.close()

        return row

    def buscar_en_contenido(self, termino):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT dp.*, dr.nombre_pdf, dr.dominio_origen, dr.fecha_hora_recepcion
            FROM documentos_procesados dp
            JOIN documentos_recibidos dr ON dp.documento_id = dr.id
            WHERE dp.contenido_json LIKE %s
            ORDER BY dp.fecha_procesamiento DESC
        """

        cursor.execute(sql, (f"%{termino}%",))
        rows = cursor.fetchall()

        for r in rows:
            r["contenido_json"] = json.loads(r["contenido_json"])

        cursor.close()
        conn.close()
        return rows

    def obtener_todos_procesados(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT dp.documento_id, dp.fecha_procesamiento, dp.version_procesamiento,
                   dr.nombre_pdf, dr.dominio_origen, dr.fecha_hora_recepcion
            FROM documentos_procesados dp
            JOIN documentos_recibidos dr ON dp.documento_id = dr.id
            ORDER BY dp.fecha_procesamiento DESC
        """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows


# Instancias globales
db_manager = DatabaseManager()
documento_recibido = DocumentoRecibido(db_manager)
documento_procesado = DocumentoProcesado(db_manager)

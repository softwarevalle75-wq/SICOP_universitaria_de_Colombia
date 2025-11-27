import os
import hashlib
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from ..config.settings import Config
from ..services.google_drive_service import google_drive_service
from ..services.pdf_processor_service import pdf_processor_service
from ..database.models import documento_recibido
from ..utils.security import validate_pdf_file
import tempfile
import threading

pdf_reception_bp = Blueprint('pdf_reception', __name__, url_prefix='/api')

@pdf_reception_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Endpoint para recibir PDFs desde dominios externos"""
    try:
        # 1. Obtener dominio de origen (solo para registro, sin bloqueo)
        origin_domain = request.headers.get('Origin') or request.headers.get('Referer', '')
        
        # 2. Verificar que se envió un archivo
        if 'pdf_file' not in request.files:
            return jsonify({
                'error': 'No se encontró archivo PDF en la solicitud',
                'codigo': 'NO_FILE_PROVIDED'
            }), 400
        
        file = request.files['pdf_file']
        
        # 3. Validar archivo
        if file.filename == '':
            return jsonify({
                'error': 'Nombre de archivo vacío',
                'codigo': 'EMPTY_FILENAME'
            }), 400
        
        # 4. Leer contenido del archivo
        file_content = file.read()
        
        # 5. Validar tamaño
        if len(file_content) > Config.MAX_FILE_SIZE:
            return jsonify({
                'error': f'Archivo demasiado grande. Máximo permitido: {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB',
                'codigo': 'FILE_TOO_LARGE'
            }), 413
        
        # 6. Validar que es un PDF válido
        if not validate_pdf_file(file_content):
            return jsonify({
                'error': 'El archivo no es un PDF válido',
                'codigo': 'INVALID_PDF'
            }), 400
        
        # 7. Generar nombre seguro y hash
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # 8. Subir a Google Drive (si está configurado)
        file_id = None
        drive_url = None
        
        if not google_drive_service.is_configured:
            print(f"Google Drive no configurado para documento: {filename}")
            return jsonify({
                'error': 'Google Drive no está configurado',
                'codigo': 'GOOGLE_DRIVE_NOT_CONFIGURED'
            }), 503
        
        print(f"Iniciando subida a Google Drive: {filename}")
        file_id, drive_url = google_drive_service.upload_pdf(
            file_content=file_content,
            filename=filename
        )
        
        if not file_id or not drive_url:
            print(f"Error: Falló la subida a Google Drive para {filename}")
            return jsonify({
                'error': 'No se pudo subir el archivo a Google Drive. Verifique la configuración de OAuth.',
                'codigo': 'DRIVE_UPLOAD_FAILED'
            }), 502
        
        print(f"Subida exitosa a Google Drive: {filename} -> {file_id}")
        
        # 9. Guardar en base de datos
        documento_id = documento_recibido.crear(
            nombre_pdf=filename,
            url_google_drive=drive_url,
            dominio_origen=origin_domain,
            tamano_archivo=len(file_content),
            hash_archivo=file_hash
        )
        
        # 10. Iniciar procesamiento en segundo plano
        processing_thread = threading.Thread(
            target=pdf_processor_service.process_pdf,
            args=(documento_id, file_content)
        )
        processing_thread.daemon = True
        processing_thread.start()
        
        # 11. Respuesta exitosa
        return jsonify({
            'success': True,
            'mensaje': 'PDF recibido y procesamiento iniciado',
            'data': {
                'documento_id': documento_id,
                'filename': filename,
                'google_drive_url': drive_url,
                'file_hash': file_hash,
                'tamano_bytes': len(file_content),
                'estado': 'procesando'
            }
        }), 201
        
    except RequestEntityTooLarge:
        return jsonify({
            'error': 'Archivo demasiado grande',
            'codigo': 'FILE_TOO_LARGE'
        }), 413
    
    except Exception as e:
        return jsonify({
            'error': f'Error interno del servidor: {str(e)}',
            'codigo': 'INTERNAL_ERROR'
        }), 500

@pdf_reception_bp.route('/document-status/<int:documento_id>', methods=['GET'])
def get_document_status(documento_id):
    """Obtiene el estado de procesamiento de un documento"""
    try:
        # Obtener información del documento
        doc_info = documento_recibido.obtener_por_id(documento_id)
        
        if not doc_info:
            return jsonify({
                'error': 'Documento no encontrado',
                'codigo': 'DOCUMENT_NOT_FOUND'
            }), 404
        
        response_data = {
            'documento_id': documento_id,
            'nombre_pdf': doc_info['nombre_pdf'],
            'estado_procesamiento': doc_info['estado_procesamiento'],
            'fecha_recepcion': doc_info['fecha_hora_recepcion'],
            'dominio_origen': doc_info['dominio_origen'],
            'google_drive_url': doc_info['url_google_drive']
        }
        
        # Si está procesado, incluir información adicional
        if doc_info['estado_procesamiento'] == 'procesado':
            from ..database.models import documento_procesado
            procesado_info = documento_procesado.obtener_por_documento_id(documento_id)
            
            if procesado_info:
                response_data['procesamiento'] = {
                    'fecha_procesamiento': procesado_info['fecha_procesamiento'],
                    'tiempo_procesamiento_segundos': procesado_info['tiempo_procesamiento_segundos'],
                    'version_procesamiento': procesado_info['version_procesamiento']
                }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estado del documento: {str(e)}',
            'codigo': 'INTERNAL_ERROR'
        }), 500

@pdf_reception_bp.route('/documents', methods=['GET'])
def list_documents():
    """Lista documentos con filtros opcionales e información procesada por IA"""
    try:
        from ..database.models import documento_procesado
        
        # Parámetros de consulta
        dominio = request.args.get('dominio')
        estado = request.args.get('estado')
        limite = int(request.args.get('limite', 50))
        offset = int(request.args.get('offset', 0))
        
        # Validar límite
        if limite > 100:
            limite = 100
        
        # Obtener documentos según filtros
        if dominio:
            documentos = documento_recibido.listar_por_dominio(dominio)
            # Aplicar paginación básica
            documentos_paginados = documentos[offset:offset + limite]
        elif estado:
            documentos = documento_recibido.listar_por_estado(estado)
            # Aplicar paginación básica
            documentos_paginados = documentos[offset:offset + limite]
        else:
            # Obtener todos los documentos con paginación
            documentos_paginados = documento_recibido.listar_todos(limite, offset)
            # Para obtener el total, necesitamos contar todos los documentos
            documentos = documento_recibido.listar_todos()
        
        # Enriquecer documentos con información procesada por IA
        documentos_enriquecidos = []
        for doc in documentos_paginados:
            # Obtener información procesada si existe
            procesado = documento_procesado.obtener_por_documento_id(doc['id'])
            
            # Crear documento enriquecido
            doc_enriquecido = dict(doc)
            # Asegurar que url_google_drive esté disponible para el frontend
            doc_enriquecido['url_google_drive'] = doc.get('url_google_drive', '')
            
            if procesado and procesado.get('contenido_json'):
                contenido = procesado['contenido_json']
                
                # Agregar el contenido_json completo
                doc_enriquecido['contenido_json'] = contenido
                
                # Agregar información de clasificación IA
                if 'classification' in contenido:
                    classification = contenido['classification']
                    doc_enriquecido['ai_info'] = {
                        'category': classification.get('category', 'otro'),
                        'summary': classification.get('summary', ''),
                        'confidence': classification.get('confidence', 0.0),
                        'keywords': classification.get('keywords', []),
                        'analysis_success': classification.get('analysis_success', False)
                    }
                
                # Agregar información de extracción
                if 'extraction' in contenido:
                    extraction = contenido['extraction']
                    doc_enriquecido['content_info'] = {
                        'total_pages': extraction.get('total_pages', 0),
                        'has_images': extraction.get('has_images', False),
                        'has_text': extraction.get('text', {}).get('has_text', False),
                        'total_chars': extraction.get('text', {}).get('total_chars', 0),
                        'images_with_text': extraction.get('images', {}).get('images_with_text', 0)
                    }
                
                # Agregar información de procesamiento
                doc_enriquecido['processing_info'] = {
                    'processed_at': procesado.get('fecha_procesamiento'),
                    'processing_time': procesado.get('tiempo_procesamiento_segundos'),
                    'version': procesado.get('version_procesamiento')
                }
            else:
                # Si no hay información procesada
                doc_enriquecido['ai_info'] = None
                doc_enriquecido['content_info'] = None
                doc_enriquecido['processing_info'] = None
            
            documentos_enriquecidos.append(doc_enriquecido)
        
        return jsonify({
            'success': True,
            'data': {
                'documentos': documentos_enriquecidos,
                'total': len(documentos),
                'limite': limite,
                'offset': offset
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al listar documentos: {str(e)}',
            'codigo': 'INTERNAL_ERROR'
        }), 500

@pdf_reception_bp.route('/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Elimina un documento específico"""
    try:
        # Verificar que el documento existe
        documento = documento_recibido.obtener_por_id(document_id)
        if not documento:
            return jsonify({
                'error': 'Documento no encontrado',
                'codigo': 'DOCUMENT_NOT_FOUND'
            }), 404
        
        # Eliminar el documento de la base de datos
        success = documento_recibido.eliminar(document_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Documento eliminado correctamente'
            }), 200
        else:
            return jsonify({
                'error': 'Error al eliminar el documento',
                'codigo': 'DELETE_FAILED'
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}',
            'codigo': 'INTERNAL_ERROR'
        }), 500

@pdf_reception_bp.route('/processing-stats', methods=['GET'])
def get_processing_stats():
    """Obtiene estadísticas de procesamiento"""
    try:
        stats = pdf_processor_service.get_processing_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Error al obtener estadísticas: {str(e)}',
            'codigo': 'INTERNAL_ERROR'
        }), 500

# Manejador de errores para archivos demasiado grandes
@pdf_reception_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({
        'error': 'Archivo demasiado grande',
        'codigo': 'FILE_TOO_LARGE',
        'max_size_mb': Config.MAX_FILE_SIZE / (1024 * 1024)
    }), 413
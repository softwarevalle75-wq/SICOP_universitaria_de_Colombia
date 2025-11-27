from flask import Blueprint, request, jsonify, session
import json
from datetime import datetime
from typing import List, Dict, Any
from ..services.chat_service import chat_service
from ..services.document_service import document_service
from ..utils.security import validate_request_headers, rate_limit_key

# Crear blueprint para rutas del chat
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Cache simple para rate limiting (en producción usar Redis)
rate_limit_cache = {}

def check_rate_limit(key: str, max_requests: int = 10, window_minutes: int = 1) -> bool:
    """Verifica rate limiting simple
    
    Args:
        key: Clave única del usuario
        max_requests: Máximo número de requests
        window_minutes: Ventana de tiempo en minutos
    
    Returns:
        True si está dentro del límite, False si excede
    """
    import time
    current_time = time.time()
    window_seconds = window_minutes * 60
    
    if key not in rate_limit_cache:
        rate_limit_cache[key] = []
    
    # Limpiar requests antiguos
    rate_limit_cache[key] = [
        timestamp for timestamp in rate_limit_cache[key]
        if current_time - timestamp < window_seconds
    ]
    
    # Verificar límite
    if len(rate_limit_cache[key]) >= max_requests:
        return False
    
    # Agregar request actual
    rate_limit_cache[key].append(current_time)
    return True

def get_specific_document(document_id: str) -> List[Dict[str, Any]]:
    """Obtiene un documento específico por su ID
    
    Args:
        document_id: ID del documento a obtener
    
    Returns:
        Lista con el documento específico (o vacía si no se encuentra)
    """
    try:
        print(f"🔎 Buscando documento específico con ID: {document_id}")
        documento = document_service.get_specific_document(document_id)
        if documento:
            print(f"✅ Documento encontrado: {documento.get('nombre_archivo', 'Sin nombre')}")
        else:
            print(f"❌ No se encontró documento con ID: {document_id}")
        return [documento] if documento else []
    except Exception as e:
        print(f"❌ Error obteniendo documento específico: {e}")
        return []

def search_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Busca documentos relevantes en la base de datos
    
    Args:
        query: Consulta de búsqueda
        limit: Número máximo de resultados
    
    Returns:
        Lista de documentos relevantes
    """
    try:
        print(f"🔍 Ejecutando búsqueda general con query: '{query}' (límite: {limit})")
        results = document_service.search_documents(query, limit)
        print(f"📊 Resultados de búsqueda: {len(results)} documentos encontrados")
        return results
    except Exception as e:
        print(f"❌ Error buscando documentos: {e}")
        return []

def generate_context_from_documents(documents: List[Dict[str, Any]]) -> str:
    """Genera contexto a partir de documentos encontrados
    
    Args:
        documents: Lista de documentos relevantes
    
    Returns:
        Contexto formateado para el chat
    """
    print(f"📝 Generando contexto desde {len(documents)} documentos")
    context = document_service.generate_context_from_documents(documents)
    print(f"✅ Contexto generado exitosamente ({len(context)} caracteres)")
    return context

def create_system_message(context: str = "") -> Dict[str, str]:
    """Crea el mensaje del sistema para el chat
    
    Args:
        context: Contexto adicional de documentos
    
    Returns:
        Mensaje del sistema formateado
    """
    return chat_service.create_system_message(context)

@chat_bp.route('/message', methods=['POST'])
def send_message():
    """Endpoint para enviar mensajes al chat"""
    try:
        # Validar headers (Content-Type para JSON)
        if not validate_request_headers(['Content-Type']):
            return jsonify({
                'error': 'Headers inválidos',
                'code': 'INVALID_HEADERS'
            }), 400
        
        # Rate limiting
        user_key = rate_limit_key(request)
        if not check_rate_limit(user_key, max_requests=20, window_minutes=5):
            return jsonify({
                'error': 'Demasiadas solicitudes. Intenta de nuevo en unos minutos.',
                'code': 'RATE_LIMIT_EXCEEDED'
            }), 429
        
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Mensaje requerido',
                'code': 'MESSAGE_REQUIRED'
            }), 400
        
        user_message = data['message'].strip()
        document_id = data.get('document_id')  # ID del documento seleccionado
        
        # LOG: Información del mensaje del usuario
        print(f"\n=== CHAT LOG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        print(f"📝 MENSAJE DEL USUARIO: {user_message}")
        print(f"📄 DOCUMENTO ESPECÍFICO: {document_id if document_id else 'No especificado (búsqueda general)'}")
        
        if not user_message:
            return jsonify({
                'error': 'El mensaje no puede estar vacío',
                'code': 'EMPTY_MESSAGE'
            }), 400

        if len(user_message) > 2000:
            return jsonify({
                'error': 'El mensaje es demasiado largo (máximo 2000 caracteres)',
                'code': 'MESSAGE_TOO_LONG'
            }), 400

        # Buscar documentos relevantes
        if document_id:
            # Si hay un documento específico seleccionado, usarlo
            relevant_docs = get_specific_document(document_id)
            print(f"🎯 BÚSQUEDA ESPECÍFICA: Documento ID {document_id}")
        else:
            # Búsqueda general en todos los documentos
            relevant_docs = search_documents(user_message, limit=5)
            print(f"🔍 BÚSQUEDA GENERAL: '{user_message}' (límite: 5 documentos)")
        
        # LOG: Documentos encontrados
        print(f"📚 DOCUMENTOS ENCONTRADOS: {len(relevant_docs)}")
        for i, doc in enumerate(relevant_docs, 1):
            doc_name = doc.get('nombre_archivo', 'Sin nombre')
            doc_id = doc.get('id', 'Sin ID')
            doc_type = doc.get('clasificacion', 'Sin clasificación')
            print(f"   {i}. {doc_name} (ID: {doc_id}, Tipo: {doc_type})")
        
        # Generar contexto completo desde la base de datos
        contexto_completo = generate_context_from_documents(relevant_docs)
        
        # LOG: Información del contexto generado
        context_length = len(contexto_completo)
        print(f"📋 CONTEXTO GENERADO: {context_length} caracteres")
        if context_length > 0:
            # Mostrar una muestra del contexto (primeros 200 caracteres)
            context_preview = contexto_completo[:200] + "..." if len(contexto_completo) > 200 else contexto_completo
            print(f"   Muestra: {context_preview}")
        else:
            print(f"   ⚠️  No se generó contexto (sin documentos relevantes)")
        
        # Usar el nuevo servicio de chat basado en base de datos
        assistant_message = chat_service.responder_chat(user_message, contexto_completo)
        
        # LOG: Respuesta generada
        response_length = len(assistant_message)
        print(f"🤖 RESPUESTA GENERADA: {response_length} caracteres")
        response_preview = assistant_message[:150] + "..." if len(assistant_message) > 150 else assistant_message
        print(f"   Muestra: {response_preview}")
        print(f"=== FIN CHAT LOG ===")
        
        # Obtener historial de conversación de la sesión
        conversation_history = session.get('chat_history', [])
        
        # Actualizar historial de conversación
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": assistant_message})
        
        # Gestionar historial usando el servicio
        conversation_history = chat_service.manage_conversation_history(conversation_history)
        
        session['chat_history'] = conversation_history
        
        return jsonify({
            'response': assistant_message,
            'relevant_documents': relevant_docs,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error en chat: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'code': 'INTERNAL_ERROR'
        }), 500

@chat_bp.route('/history', methods=['GET'])
def get_chat_history():
    """Obtiene el historial de chat de la sesión"""
    try:
        history = session.get('chat_history', [])
        
        return jsonify({
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'code': 'INTERNAL_ERROR'
        }), 500

@chat_bp.route('/clear', methods=['POST'])
def clear_chat_history():
    """Limpia el historial de chat de la sesión"""
    try:
        session.pop('chat_history', None)
        
        return jsonify({
            'message': 'Historial de chat limpiado',
            'success': True
        })
        
    except Exception as e:
        print(f"Error limpiando historial: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'code': 'INTERNAL_ERROR'
        }), 500

@chat_bp.route('/search', methods=['POST'])
def search_documents_endpoint():
    """Endpoint para buscar documentos específicos"""
    try:
        # Rate limiting
        user_key = rate_limit_key(request)
        if not check_rate_limit(user_key, max_requests=30, window_minutes=5):
            return jsonify({
                'error': 'Demasiadas solicitudes. Intenta de nuevo en unos minutos.',
                'code': 'RATE_LIMIT_EXCEEDED'
            }), 429
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Query de búsqueda requerida',
                'code': 'QUERY_REQUIRED'
            }), 400
        
        query = data['query'].strip()
        limit = min(data.get('limit', 10), 50)  # Máximo 50 resultados
        
        if not query:
            return jsonify({
                'error': 'La consulta no puede estar vacía',
                'code': 'EMPTY_QUERY'
            }), 400
        
        # Buscar documentos
        documents = search_documents(query, limit)
        
        return jsonify({
            'documents': documents,
            'count': len(documents),
            'query': query
        })
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'code': 'INTERNAL_ERROR'
        }), 500

@chat_bp.route('/stats', methods=['GET'])
def get_chat_stats():
    """Obtiene estadísticas del chat y documentos"""
    try:
        # Estadísticas de documentos
        total_docs = DocumentoProcesado.contar_total()
        docs_por_clasificacion = DocumentoProcesado.contar_por_clasificacion()
        
        # Estadísticas de sesión
        history_count = len(session.get('chat_history', []))
        
        return jsonify({
            'documents': {
                'total': total_docs,
                'by_classification': docs_por_clasificacion
            },
            'session': {
                'messages_count': history_count
            }
        })
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'code': 'INTERNAL_ERROR'
        }), 500
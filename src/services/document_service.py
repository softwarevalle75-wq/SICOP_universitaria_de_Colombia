from typing import List, Dict, Any, Optional
from ..database.models import documento_procesado

class DocumentService:
    """Servicio para manejar operaciones con documentos"""
    
    def get_specific_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un documento específico por su ID
        
        Args:
            document_id: ID del documento a obtener
            
        Returns:
            Información del documento o None si no existe
        """
        try:
            documento = documento_procesado.obtener_por_documento_id(int(document_id))
            if documento:
                contenido_json = documento.get('contenido_json', {})
                if isinstance(contenido_json, str):
                    import json
                    try:
                        contenido_json = json.loads(contenido_json)
                    except:
                        contenido_json = {}
                
                return {
                    'documento_id': documento['documento_id'],
                    'nombre_pdf': documento['nombre_pdf'],
                    'dominio_origen': documento.get('dominio_origen', ''),
                    'fecha_procesamiento': documento['fecha_procesamiento'],
                    'contenido_json': contenido_json,
                    'relevancia': 1.0
                }
            return None
        except Exception as e:
            raise Exception(f"Error obteniendo documento específico: {str(e)}")
    
    def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca documentos por contenido
        
        Args:
            query: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            Lista de documentos encontrados
        """
        try:
            documentos = documento_procesado.buscar_en_contenido(query)
            documentos = documentos[:limit]
            
            resultados = []
            for doc in documentos:
                contenido_json = doc.get('contenido_json', {})
                if isinstance(contenido_json, str):
                    import json
                    try:
                        contenido_json = json.loads(contenido_json)
                    except:
                        contenido_json = {}
                
                resultados.append({
                    'documento_id': doc['documento_id'],
                    'nombre_pdf': doc['nombre_pdf'],
                    'dominio_origen': doc.get('dominio_origen', ''),
                    'fecha_procesamiento': doc['fecha_procesamiento'],
                    'contenido_json': contenido_json,
                    'relevancia': 0.7
                })
            
            return resultados
        except Exception as e:
            raise Exception(f"Error en búsqueda de documentos: {str(e)}")
    
    def generate_context_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Genera contexto formateado a partir de documentos con información por páginas
        
        Args:
            documents: Lista de documentos
            
        Returns:
            Contexto formateado como string con referencias de páginas
        """
        if not documents:
            return "No se encontraron documentos relevantes para responder la pregunta."
        
        context_parts = []
        for doc in documents:
            context_part = f"""DOCUMENTO: {doc['nombre_pdf']}"""
            
            # Agregar información de clasificación SGDEA si está disponible
            contenido_json = doc.get('contenido_json')
            if contenido_json and isinstance(contenido_json, dict):
                # Información SGDEA
                sgdea = contenido_json.get('classification_sgdea', {})
                if sgdea:
                    context_part += f"\nTipo: {sgdea.get('tipologia_documental', 'Documento')}"
                    context_part += f"\nAsunto: {sgdea.get('asunto', 'Sin asunto')}"
                
                # Contenido extraído por páginas (texto directo + OCR de imágenes)
                extraction = contenido_json.get('extraction', {})
                texto_extraido = extraction.get('text', {})
                imagenes_extraidas = extraction.get('images', {})
                
                # Organizar todo el contenido por páginas
                contenido_por_pagina = {}
                
                # Agregar texto directo por páginas
                if texto_extraido:
                    for pagina, contenido in texto_extraido.items():
                        if isinstance(contenido, str) and contenido.strip():
                            if pagina not in contenido_por_pagina:
                                contenido_por_pagina[pagina] = {'texto': '', 'imagenes': []}
                            contenido_por_pagina[pagina]['texto'] = contenido.strip()
                
                # Agregar texto OCR de imágenes por páginas
                if imagenes_extraidas:
                    # Verificar si hay imágenes con texto OCR
                    imagenes_info = imagenes_extraidas.get('images', [])
                    if isinstance(imagenes_info, list):
                        for img_info in imagenes_info:
                            if isinstance(img_info, dict):
                                pagina = str(img_info.get('page', 'unknown'))
                                ocr_text = img_info.get('ocr_text', '')
                                if ocr_text and ocr_text.strip():
                                    if pagina not in contenido_por_pagina:
                                        contenido_por_pagina[pagina] = {'texto': '', 'imagenes': []}
                                    # Solo agregar OCR si no hay texto directo o es diferente
                                    if not contenido_por_pagina[pagina]['texto'] or len(ocr_text.strip()) > len(contenido_por_pagina[pagina]['texto']):
                                        contenido_por_pagina[pagina]['texto'] = ocr_text.strip()
                                    contenido_por_pagina[pagina]['imagenes'].append({
                                        'index': img_info.get('image_index', 0),
                                        'has_text': img_info.get('has_text', False),
                                        'dimensions': f"{img_info.get('width', 0)}x{img_info.get('height', 0)}"
                                    })
                
                # Mostrar contenido organizado por páginas
                if contenido_por_pagina:
                    context_part += "\n\nCONTENIDO POR PÁGINAS:"
                    for pagina in sorted(contenido_por_pagina.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
                        info_pagina = contenido_por_pagina[pagina]
                        context_part += f"\n\nPÁGINA {pagina}:"
                        
                        # Agregar texto completo (sin limitaciones)
                        if info_pagina['texto']:
                            context_part += f"\n{info_pagina['texto']}"
                        
                        # Agregar información de imágenes si existen
                        if info_pagina['imagenes']:
                            context_part += f"\n[Contiene {len(info_pagina['imagenes'])} imagen(es)]"
            
            context_parts.append(context_part)
        
        return "\n\n" + "="*50 + "\n\n".join(context_parts) + "\n\n" + "="*50

# Instancia global del servicio
document_service = DocumentService()
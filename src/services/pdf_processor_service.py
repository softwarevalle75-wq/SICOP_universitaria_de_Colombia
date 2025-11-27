import json
import time
from typing import Dict, Any, List
from datetime import datetime
from ..database.models import documento_recibido, documento_procesado
from ..utils.pdf_extractor import pdf_extractor
from .document_classifier import document_classifier

class PDFProcessorService:
    """Servicio para procesar documentos PDF con extracción de texto e imágenes"""
    
    def __init__(self):
        self.version = "2.0"
    
    def process_pdf(self, documento_id: int, file_content: bytes) -> bool:
        """Procesa un PDF extrayendo texto, imágenes y clasificándolo
        
        Args:
            documento_id: ID del documento en la base de datos
            file_content: Contenido del archivo PDF en bytes
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            start_time = time.time()
            
            # Actualizar estado a 'procesando'
            documento_recibido.actualizar_estado(documento_id, 'procesando')
            
            print(f"Iniciando procesamiento del documento {documento_id}...")
            
            # 1. Extraer contenido del PDF (texto e imágenes)
            print(f"Extrayendo contenido del PDF...")
            extracted_content = pdf_extractor.extract_content(file_content)
            
            if not extracted_content.get("extraction_success", False):
                raise Exception(f"Error en extracción: {extracted_content.get('error', 'Error desconocido')}")
            
            # 2. Clasificar documento usando IA con formato SGDEA
            print(f"Clasificando documento con IA (SGDEA)...")
            classification_result = document_classifier.clasificacion_por_paginas(extracted_content)
            
            # 3. Preparar contenido procesado con clasificación SGDEA
            processed_content = {
                "extraction": {
                    "text": extracted_content.get("text", {}),
                    "images": extracted_content.get("images", {}),
                    "metadata": extracted_content.get("metadata", {}),
                    "total_pages": extracted_content.get("total_pages", 0),
                    "has_images": extracted_content.get("has_images", False)
                },
                "classification_sgdea": {
                    "unidad_administrativa": classification_result.get("unidad_administrativa", "No identificada"),
                    "asunto": classification_result.get("asunto", "Sin asunto"),
                    "serie_documental": classification_result.get("serie_documental", "Otros"),
                    "subserie_documental": classification_result.get("subserie_documental", "No aplica"),
                    "tipologia_documental": classification_result.get("tipologia_documental", "Documento"),
                    "metadatos": classification_result.get("metadatos", []),
                    "contenido_relevante": classification_result.get("contenido_relevante", True),
                    "analysis_success": classification_result.get("analysis_success", False)
                },
                "processing_info": {
                    "version": self.version,
                    "timestamp": datetime.now().isoformat(),
                    "file_size_bytes": len(file_content),
                    "classification_format": "SGDEA"
                }
            }
            
            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            
            print(f"Procesamiento completado en {processing_time:.2f} segundos")
            
            # 4. Guardar resultado del procesamiento
            documento_procesado.crear(
                documento_id=documento_id,
                contenido_json=processed_content,
                tiempo_procesamiento=processing_time,
                version=self.version
            )
            
            # 5. Actualizar estado a 'procesado'
            documento_recibido.actualizar_estado(documento_id, 'procesado')
            
            print(f"Documento {documento_id} procesado exitosamente")
            return True
            
        except Exception as e:
            print(f"Error procesando PDF {documento_id}: {e}")
            # Actualizar estado a 'error'
            documento_recibido.actualizar_estado(documento_id, 'error')
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento
        
        Returns:
            Dict con estadísticas de procesamiento
        """
        try:
            # Obtener todos los documentos procesados
            procesados = documento_procesado.obtener_todos_procesados()
            
            # Calcular estadísticas básicas
            total_procesados = len(procesados)
            
            # Contar por estado
            pendientes = len(documento_recibido.listar_pendientes())
            
            return {
                "total_procesados": total_procesados,
                "pendientes": pendientes,
                "version_procesamiento": self.version,
                "ultima_actualizacion": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                "error": str(e),
                "total_procesados": 0,
                "pendientes": 0
            }

# Instancia global del servicio
pdf_processor_service = PDFProcessorService()
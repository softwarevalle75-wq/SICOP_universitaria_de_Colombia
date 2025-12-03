import os
import google.generativeai as genai
from typing import Dict, Any, List
from ..config.settings import Config

# Configurar cliente Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

class DocumentClassifier:
    """Clasificador de documentos usando Gemini"""

    def __init__(self):
        self.model_name = Config.GEMINI_MODEL

    def classify_document(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica un documento basado en su contenido usando parámetros SGDEA

        Args:
            content: Contenido extraído del PDF (texto, OCR, metadatos)

        Returns:
            Dict con clasificación según parámetros SGDEA
        """
        try:
            # Preparar el texto completo para análisis
            full_text = self._prepare_text_for_analysis(content)

            if not full_text.strip():
                return {
                    "documento_completo": True,
                    "unidad_administrativa": "Sin especificar",
                    "asunto": "Documento sin contenido",
                    "serie_documental": "Otros",
                    "subserie_documental": "General",
                    "tipologia_documental": "Carta",
                    "metadatos": [],
                    "contenido_relevante": "No",
                    "analysis_success": False
                }

            return self.clasificacion_por_paginas(full_text)

        except Exception as e:
            return {
                "documento_completo": True,
                "unidad_administrativa": "Sin especificar",
                "asunto": f"Error: {str(e)}",
                "serie_documental": "Otros",
                "subserie_documental": "General",
                "tipologia_documental": "Carta",
                "metadatos": [],
                "contenido_relevante": "No",
                "error": str(e),
                "analysis_success": False
            }

    def _prepare_text_for_analysis(self, content: Dict[str, Any]) -> str:
        """Prepara el texto completo para análisis"""
        text_parts = []

        # Texto directo del PDF
        if content.get("text", {}).get("full_text"):
            text_parts.append("TEXTO DEL DOCUMENTO:")
            text_parts.append(content["text"]["full_text"])

        # Texto de OCR de imágenes
        if content.get("images", {}).get("ocr_text"):
            text_parts.append("\nTEXTO DE IMÁGENES (OCR):")
            text_parts.append(content["images"]["ocr_text"])

        return "\n".join(text_parts)

    def clasificacion_por_paginas(self, texto_completo: str) -> Dict[str, Any]:
        """Función para clasificar documento completo según parámetros SGDEA

        Args:
            texto_completo (str): Texto completo del documento

        Returns:
            dict: Diccionario con clasificación del documento completo
        """
        clasificaciones = {}

        # Procesar todo el documento como una unidad
        texto_pagina = texto_completo

        # Crear prompt para el documento completo
        prompt = f"""Eres un asistente especializado en clasificación documental.

Eres un asistente de clasificación documental para una entidad importante. Tu tarea consiste en analizar el siguiente texto completo de un documento para identificar y clasificar la información clave.

Texto completo del documento a analizar:
{texto_pagina}

Extrae y clasifica la siguiente información según los parámetros de un Sistema de Gestión y Archivo (SGDEA):
1. **Unidad administrativa:** Identifica el área o departamento responsable (por ejemplo, 'Secretaria de Hacienda', 'Departamento de Tránsito'). Si no se menciona, usa 'Sin especificar'.
2. **Asunto:** Resume el tema principal del documento en no más de 10 palabras.
3. **Serie documental:** Basándote en el contenido, clasifica la información en una de las siguientes categorías: 'Peticiones', 'Quejas', 'Reclamos', 'Sugerencias', 'Felicitaciones'. Si no aplica, usa 'Otros'.
4. **Subserie documental:** Ofrece una subcategoría más específica para la serie (por ejemplo, para 'Peticiones', podría ser 'Trámites de Licencia'). Si no se puede determinar, usa 'General'.
5. **Tipología documental:** Identifica el tipo de documento (ej. 'Solicitud de información', 'Oficio', 'Carta'). Si no se puede, usa 'Carta'.
6. **Metadatos:** Extrae palabras clave o frases relevantes que describan el contenido del documento (por ejemplo, 'licencia de construcción', 'demora en proceso').
7. **Contenido relevante:** Indica si el documento contiene información sustancial ('Sí') o es principalmente formato/encabezados ('No').

Proporciona la respuesta únicamente en formato JSON. El JSON debe tener la siguiente estructura:
{{
  "documento_completo": true,
  "unidad_administrativa": "...",
  "asunto": "...",
  "serie_documental": "...",
  "subserie_documental": "...",
  "tipologia_documental": "...",
  "metadatos": [...],
  "contenido_relevante": "..."
}}"""

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)

            respuesta_str = response.text

            try:
                import json
                # Limpiar la respuesta si viene con markdown
                respuesta_limpia = respuesta_str.strip()
                if respuesta_limpia.startswith("```json"):
                    respuesta_limpia = respuesta_limpia[7:]
                if respuesta_limpia.startswith("```"):
                    respuesta_limpia = respuesta_limpia[3:]
                if respuesta_limpia.endswith("```"):
                    respuesta_limpia = respuesta_limpia[:-3]
                respuesta_limpia = respuesta_limpia.strip()

                clasificacion_json = json.loads(respuesta_limpia)
                clasificaciones["documento_completo"] = clasificacion_json
                clasificacion_json["analysis_success"] = True
                return clasificacion_json
            except json.JSONDecodeError:
                clasificaciones["documento_completo"] = {"error": "JSON inválido", "respuesta_raw": respuesta_str}
                return {
                    "documento_completo": True,
                    "unidad_administrativa": "Sin especificar",
                    "asunto": "Error en procesamiento",
                    "serie_documental": "Otros",
                    "subserie_documental": "General",
                    "tipologia_documental": "Carta",
                    "metadatos": [],
                    "contenido_relevante": "No",
                    "error": "JSON inválido",
                    "analysis_success": False
                }

        except Exception as e:
            clasificaciones["documento_completo"] = {"error": f"Error en clasificación: {str(e)}"}
            return {
                "documento_completo": True,
                "unidad_administrativa": "Sin especificar",
                "asunto": "Error en clasificación",
                "serie_documental": "Otros",
                "subserie_documental": "General",
                "tipologia_documental": "Carta",
                "metadatos": [],
                "contenido_relevante": "No",
                "error": str(e),
                "analysis_success": False
            }



# Instancia global del clasificador
document_classifier = DocumentClassifier()

import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any

# Cargar variables de entorno
load_dotenv()

# Configurar cliente Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class ChatService:
    def __init__(self):
        self.max_history_length = 10  # Reducido para simplicidad
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    def responder_con_contexto_ia(self, pregunta: str, contexto_completo: str) -> str:
        """Responde usando ÚNICAMENTE el contexto del documento"""
        if not contexto_completo or "No se encontraron documentos" in contexto_completo:
            return "No tengo información en los documentos para responder esa pregunta."

        prompt = f"""INSTRUCCIONES CRÍTICAS - DEBES SEGUIR AL PIE DE LA LETRA:

1. ANÁLISIS EXHAUSTIVO OBLIGATORIO:
   - Revisa ABSOLUTAMENTE TODO el contenido del documento
   - Lee CADA página completa sin saltarte NINGUNA información
   - Examina TODO el texto de TODAS las páginas proporcionadas
   - NO te limites a buscar solo palabras clave
   - Analiza el contenido completo de principio a fin

2. REGLAS DE RESPUESTA:
   - Responde ÚNICAMENTE con información que esté EXPLÍCITAMENTE en el documento
   - Si encuentras la información, especifica EXACTAMENTE en qué página está
   - Si después de revisar TODO el documento no encuentras la información, di "No se encuentra esa información en el documento"
   - NO agregues conocimiento externo
   - NO hagas inferencias o suposiciones
   - Sé específico y cita la página exacta

3. PROCESO OBLIGATORIO:
   - Primero: Lee TODO el contenido de TODAS las páginas
   - Segundo: Busca la información solicitada en TODO el contenido
   - Tercero: Si la encuentras, responde con la página específica
   - Cuarto: Si no la encuentras después de revisar TODO, di que no está

DOCUMENTO COMPLETO A ANALIZAR:
{contexto_completo}

PREGUNTA: {pregunta}

RESPUESTA (después de revisar TODO el documento):"""

        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)

        return response.text.strip()

    def responder_chat(self, pregunta: str, contexto: str = "") -> str:
        """Función principal: Responde usando todo el contexto"""
        try:
            # Responder con todo el contexto
            respuesta = self.responder_con_contexto_ia(pregunta, contexto)
            return respuesta
        except Exception as e:
            return f"Error: {str(e)} Api Key"



    def create_system_message(self, context: str = "") -> Dict[str, str]:
        """Mantener compatibilidad - método simplificado"""
        return {"role": "system", "content": "Asistente de documentos"}

    def manage_conversation_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Gestiona el historial de conversación de forma simple"""
        if len(history) > self.max_history_length:
            return history[-self.max_history_length:]
        return history

# Instancia global del servicio
chat_service = ChatService()

import os
from openai import OpenAI
from typing import List, Dict, Any

# NO USAR load_dotenv EN PRODUCCIÓN

class ChatService:
    def __init__(self):
        self.max_history_length = 10

        # Cargar API KEY directamente desde entorno
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            print("⚠️ ERROR: OPENAI_API_KEY no está definida en Railway")
        
        self.client = OpenAI(api_key=api_key)

    def responder_con_contexto_ia(self, pregunta: str, contexto_completo: str) -> str:
        if not contexto_completo:
            return "No tengo información suficiente para responder."

        prompt = f"""
INSTRUCCIONES:
( ... tus reglas ... )

DOCUMENTO COMPLETO:
{contexto_completo}

PREGUNTA: {pregunta}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    def responder_chat(self, pregunta: str, contexto: str = "") -> str:
        try:
            return self.responder_con_contexto_ia(pregunta, contexto)
        except Exception as e:
            return f"Error: {str(e)}"

chat_service = ChatService()

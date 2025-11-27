import re
from typing import List
from flask import request


def validate_domain(origin_domain: str) -> bool:
    """Permite todos los orígenes (sin restricción)."""
    return True


def validate_pdf_file(file_content: bytes) -> bool:
    """Valida si el contenido es un archivo PDF válido
    
    Args:
        file_content: Contenido del archivo en bytes
        
    Returns:
        bool: True si es un PDF válido
    """
    if not file_content:
        return False
    
    # Verificar que comience con la firma PDF
    pdf_signature = b'%PDF-'
    if not file_content.startswith(pdf_signature):
        return False
    
    # Verificar tamaño mínimo (un PDF válido debe tener al menos algunos bytes)
    if len(file_content) < 100:
        return False
    
    return True


def validate_request_headers(required_headers: List[str] = None) -> bool:
    """Valida headers requeridos en la solicitud
    
    Args:
        required_headers: Lista de headers requeridos
        
    Returns:
        bool: True si todos los headers están presentes
    """
    if not required_headers:
        return True
    
    for header in required_headers:
        if header not in request.headers:
            return False
    
    return True


def rate_limit_key(request_obj) -> str:
    """Genera una clave única para rate limiting
    
    Args:
        request_obj: Objeto request de Flask
        
    Returns:
        str: Clave única para el usuario/IP
    """
    # Usar IP del cliente como clave
    client_ip = request_obj.environ.get('HTTP_X_FORWARDED_FOR', request_obj.remote_addr)
    if client_ip:
        # Si hay múltiples IPs (proxy), usar la primera
        client_ip = client_ip.split(',')[0].strip()
    
    return f"rate_limit:{client_ip}"


def sanitize_filename(filename: str) -> str:
    """Sanitiza un nombre de archivo
    
    Args:
        filename: Nombre de archivo original
        
    Returns:
        str: Nombre de archivo sanitizado
    """
    # Remover caracteres peligrosos
    dangerous_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(dangerous_chars, '_', filename)
    
    # Limitar longitud
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        sanitized = name[:max_name_length] + ('.' + ext if ext else '')
    
    return sanitized
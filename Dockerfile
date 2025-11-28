FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema PRIMERO
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    mupdf \
    mupdf-tools \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar modelo de spaCy para español
RUN python -m spacy download es_core_news_sm

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash appuser

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Crear directorios necesarios con permisos correctos
RUN mkdir -p uploads temp data && chown -R appuser:appuser uploads temp data

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 🚀 CMD final: recrea token.json si existe GOOGLE_TOKEN_JSON y luego arranca Gunicorn
CMD ["bash", "-c", "if [ -n \"$GOOGLE_TOKEN_JSON\" ]; then echo \"$GOOGLE_TOKEN_JSON\" > /app/src/token.json; fi; exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app:app"]


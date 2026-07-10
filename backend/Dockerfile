# Backend Dockerfile com Tesseract e Poppler para Linux
FROM python:3.12-slim

# Metadados
LABEL maintainer="Sistema de Advocacia"
LABEL description="Backend Django com suporte a OCR (Tesseract) e análise de IA"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app


# Instalar dependências do sistema
# - tesseract-ocr: OCR engine
# - tesseract-ocr-por: Pacote de idioma português
# - poppler-utils: Para converter PDF em imagens
# - libpq-dev: Para PostgreSQL
# - gcc: Compilador necessário para alguns pacotes Python
# - ffmpeg: Conversão e processamento de áudio/vídeo
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libpq-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Verificar instalação do Tesseract
RUN tesseract --version && \
    tesseract --list-langs | grep por && \
    echo "✅ Tesseract instalado com suporte a português"

# Copiar requirements
COPY backend/requirements.txt .

# Instalar dependências Python (sem torch/easyocr para economizar memória)
# pypdf já está no requirements.txt e é suficiente para PDFs digitais
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código da aplicação
COPY backend/ ./

# Criar diretórios para arquivos estáticos e media
RUN mkdir -p /app/staticfiles /app/media

# Coletar arquivos estáticos (opcional, pode ser feito no entrypoint)
# RUN python manage.py collectstatic --noinput

# Expor porta
EXPOSE 8000

# Script de entrada (entrypoint)
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r$//g' /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "300", "--worker-connections", "1000"]

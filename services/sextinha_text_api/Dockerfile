FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# (Opcional) pacotes de sistema úteis
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Instala as dependências do serviço TEXT
COPY services/sextinha_text_api/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copia o projeto inteiro (inclui shared/, tenants/, etc.)
COPY . /app

EXPOSE 8000

# ✅ Healthcheck em forma exec (compatível)
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=20s \
  CMD ["python", "-c", "import socket,sys; s=socket.create_connection(('127.0.0.1',8000),2); s.close()"]

# Comando
CMD ["uvicorn", "services.sextinha_text_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

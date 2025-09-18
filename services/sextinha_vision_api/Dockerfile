# syntax=docker/dockerfile:1
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# deps mínimas de sistema
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependências Python essenciais para API
# (Se você tiver requirements.txt próprio do vision, use COPY + pip -r)
RUN pip install fastapi uvicorn pydantic pillow

# Copiar o pacote services inteiro (inclui shared e o próprio vision)
# OBS: O build context deve ser a RAIZ do repositório.
COPY services/__init__.py ./services/__init__.py
COPY services/shared ./services/shared
COPY services/sextinha_vision_api/__init__.py ./services/sextinha_vision_api/__init__.py
COPY services/sextinha_vision_api/app ./services/sextinha_vision_api/app

# Tornar 'services' importável (resolve from services.shared...)
ENV PYTHONPATH=/app

# usuário não-root
RUN useradd -m appuser
USER appuser

# Porta distinta do text
EXPOSE 8001

# Entrypoint
CMD ["uvicorn", "services.sextinha_vision_api.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

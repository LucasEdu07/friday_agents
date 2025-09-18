# syntax=docker/dockerfile:1

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

# Diretório raiz da app dentro do container
WORKDIR /app

# (Opcional) se tiver um requirements.txt do serviço, use-o.
# Para começar simples, instalamos deps essenciais diretamente:
RUN pip install fastapi uvicorn pydantic

# IMPORTANTE: Agora estamos assumindo que o build context é a RAIZ do repo.
# Copiamos o pacote completo "services" (inclui shared e sextinha_text_api).
COPY services/__init__.py ./services/__init__.py
COPY services/shared ./services/shared
COPY services/sextinha_text_api/__init__.py ./services/sextinha_text_api/__init__.py
COPY services/sextinha_text_api/app ./services/sextinha_text_api/app

# PYTHONPATH aponta para /app para resolver "services.*"
ENV PYTHONPATH=/app

# Usuário não-root
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Aponte o módulo completo (pacote) para o uvicorn
CMD ["uvicorn", "services.sextinha_text_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

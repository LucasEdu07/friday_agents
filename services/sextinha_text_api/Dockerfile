FROM python:3.11-slim

WORKDIR /app

# Copia o código
COPY services/__init__.py ./services/__init__.py
COPY services/shared ./services/shared
COPY services/sextinha_text_api/__init__.py ./services/sextinha_text_api/__init__.py
COPY services/sextinha_text_api/app ./services/sextinha_text_api/app

# Depêndencias necessárias (inclui psycopg)
RUN pip install --no-cache-dir fastapi uvicorn pydantic "psycopg[binary]~=3.2"

EXPOSE 8000

# Sobe o uvicorn ouvindo em 0.0.0.0
CMD ["uvicorn", "services.sextinha_text_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

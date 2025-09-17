# Sextinha Vision API

API em **FastAPI** para validação/inspeção simples de imagens (base64).

## 🚀 Rodar local
```bash
uvicorn services.sextinha_vision_api.app.main:app --reload --host 127.0.0.1 --port 8081
```

## 🔎 Endpoints
- `GET /health` → `{"status":"ok","service":"sextinha_vision_api"}`
- `POST /vision/analyze` → `{"size_bytes": int, "format": "png|jpeg|unknown"}`

### Modelo de request
```json
{ "image_base64": "<base64 válido>" }
```

### Exemplos
- Base64 válido (não-imagem):
```json
{ "image_base64": "aGVsbG8gdmJzCg==" }
```
- PNG 1x1 transparente:
```json
{ "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/5+BAQACAgEA9lK2WQAAAABJRU5ErkJggg==" }
```

### Exemplo de resposta
```json
{ "size_bytes": 67, "format": "png" }
```

## 🧪 Testes
```bash
pytest -q
```

## 🧰 Dev
- FastAPI + **Pydantic v2**
- Schemas em `app/models.py`
- Base de validação: `services/shared/models.py`
- Validação de base64 no schema; endpoint apenas decodifica e detecta assinatura (PNG/JPEG)

## 📚 Docs
- Swagger: `http://127.0.0.1:8081/docs`
- OpenAPI: `http://127.0.0.1:8081/openapi.json`

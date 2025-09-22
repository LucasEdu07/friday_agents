# Sextinha Text API

Pequena API em **FastAPI** para análise simples de texto.

## 🚀 Rodar local
```bash
uvicorn services.sextinha_text_api.app.main:app --reload --host 127.0.0.1 --port 8080
```

## 🔎 Endpoints
- `GET /health` → `{"status":"ok","service":"sextinha_text_api"}`
- `POST /analyze` → `{"length": int, "word_count": int, "preview": str}`

### Modelo de request
```json
{ "text": "Sextinha é braba demais!" }
```

### Exemplo de resposta
```json
{
  "length": 26,
  "word_count": 4,
  "preview": "Sextinha é braba demais!"
}
```

## 🧪 Testes
```bash
pytest -q
```

## 🧰 Dev
- FastAPI + **Pydantic v2**
- Schemas em `app/models.py`
- Base de validação compartilhada: `services/shared/models.py` (`AppBaseModel`, `extra="forbid"`)
- `word_count` via regex; `preview` corta em 120 chars com `…`

## 📚 Docs
- Swagger: `http://127.0.0.1:8080/docs`
- OpenAPI: `http://127.0.0.1:8080/openapi.json`

## Autenticação (v1)
As rotas **/v1/** exigem cabeçalho `x-api-key`. Exemplos de tenants seeded:

- `camila123` → Dra. Camila
- `zeoficina456` → Oficina do Zé
- `squad789` → Squad Inc

No Swagger (`/docs`), use o botão **Authorize**:
- **apiKey**: `camila123` (ou outra)

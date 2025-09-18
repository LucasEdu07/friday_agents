# 🧠 Sextinha Agents (a.k.a. `friday_agents`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange)
![Offline Ready](https://img.shields.io/badge/offline-ready-brightgreen)
[![CI](https://github.com/LucasEdu07/friday_agents/actions/workflows/ci.yml/badge.svg)](https://github.com/LucasEdu07/friday_agents/actions/workflows/ci.yml)

> **Sextinha Agents** é um projeto com duas APIs minimalistas (**texto** e **visão**) focado em **DevEx** e **deploy local**.
> A Sprint 02 adiciona: **Dockerfiles**, **Docker Compose**, **/health e /readiness**, **CI (ruff/mypy/pytest)** e **pre-commit**.

---

## ✨ Visão Geral

- 💾 **Shared**: utilitários/modelos compartilhados para as APIs.
- 🧠 **Text API**: análise simples de texto via FastAPI.
- 🖼️ **Vision API**: análise simples de imagem base64 (detecção de formato/tamanho).
- 📡 **API REST**: endpoints versionados, com documentação (Swagger) e testes.
- 🧩 **Arquitetura modular** pronta para evoluir com novos serviços.

---

## 📂 Estrutura do Projeto

```
friday_agents/
├── requests/
│   ├── text.http
│   ├── text_analyze.http
│   ├── vision.http
│   └── vision_analyze.http
├── services/
│   ├── sextinha_text_api/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── models.py
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   └── __init__.py
│   ├── sextinha_vision_api/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── models.py
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   └── __init__.py
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── health.py            # helper para /health e /readiness
│   │   ├── models.py
│   │   └── settings.py
│   └── __init__.py
├── tests/
│   └── services/
│       ├── sextinha_text_api/
│       │   └── test_analyze.py
│       └── sextinha_vision_api/
│           └── test_health.py
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── docker-compose.yml
├── .env.example
├── mypy.ini
├── ruff.toml
├── pytest.ini
└── run_all.sh
```

---

## 🔧 Pré-requisitos

- **Python 3.11+** (para rodar local sem Docker)
- **Docker** + **Docker Compose v2**
  - Windows/macOS: **Docker Desktop** (WSL 2 habilitado no Windows)
- (Opcional) **pre-commit** para hooks locais

Verifique:
```bash
docker version
docker compose version
```

---

## 🧪 Ambiente local (sem Docker)

> Útil para debug rápido; para padronizar, use Docker/Compose.

```bash
# Na raiz
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1

pip install -r .ci/requirements.txt
# Permitir imports do pacote "services"
# Linux/macOS:
export PYTHONPATH=$(pwd)
# Windows PowerShell:
# $env:PYTHONPATH = (Get-Location)

# Text API
uvicorn services.sextinha_text_api.app.main:app --host 0.0.0.0 --port 8000
# Vision API
uvicorn services.sextinha_vision_api.app.main:app --host 0.0.0.0 --port 8001
```

---

## 🐳 Rodando com Docker

> **Sempre faça o build a partir da raiz** (os Dockerfiles estão nos serviços, mas o projeto importa `services.*`).

### Build/Run por serviço

**Text**
```bash
docker build -f services/sextinha_text_api/Dockerfile -t sextinha-text:dev .
docker run --rm -p 8000:8000 sextinha-text:dev
```

**Vision**
```bash
docker build -f services/sextinha_vision_api/Dockerfile -t sextinha-vision:dev .
docker run --rm -p 8001:8001 sextinha-vision:dev
```

### Subindo tudo com Docker Compose

`.env.example` (na raiz):
```env
TEXT_PORT=8000
VISION_PORT=8001
```

Crie seu `.env` (opcional) e ajuste portas:
```bash
cp .env.example .env
```

Rodando:
```bash
docker compose build
docker compose up -d
docker compose ps
# logs
docker compose logs -f text
docker compose logs -f vision
# encerrar
docker compose down
```

---

## 📚 Endpoints

| Serviço | Método | Rota                | Descrição                                               |
|--------:|:------:|---------------------|---------------------------------------------------------|
|   text  |  GET   | `/health`           | Liveness (processo ativo)                               |
|   text  |  GET   | `/readiness`        | Readiness (pronto para tráfego)                         |
|   text  |  POST  | `/analyze`          | Analisa texto (tamanho, contagem de palavras, preview)  |
| vision  |  GET   | `/health`           | Liveness                                                |
| vision  |  GET   | `/readiness`        | Readiness                                               |
| vision  |  POST  | `/vision/analyze`   | Analisa imagem base64 (formato e tamanho)               |

**Exemplos (bash):**
```bash
# Text
curl http://localhost:${TEXT_PORT:-8000}/readiness
curl -X POST http://localhost:${TEXT_PORT:-8000}/analyze   -H "Content-Type: application/json"   -d '{"text":"Hello Sextinha Agents!"}'

# Vision
curl http://localhost:${VISION_PORT:-8001}/readiness
curl -X POST http://localhost:${VISION_PORT:-8001}/vision/analyze   -H "Content-Type: application/json"   -d '{"image_base64":"<BASE64>"}'
```

**Windows PowerShell (evitar alias do Invoke-WebRequest):**
```powershell
curl.exe http://localhost:8000/readiness
curl.exe http://localhost:8001/readiness
```

**Arquivos `.http`:**
- Em `requests/` (VS Code REST Client / JetBrains HTTP Client).

---

## ✅ Testes e Qualidade

```bash
# Testes
pytest -q

# Lint
ruff check .

# Type-check
mypy services tests

# Pre-commit
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
- **CI (GitHub Actions)**: executa **ruff**, **mypy** e **pytest** em push/PR para `main` e `develop`.

---

## 🛠️ Troubleshooting

- **`docker: command not found`**
  - Inicie o Docker Desktop (Windows/macOS) e/ou reabra o terminal.
  - Windows: confira WSL 2 (`wsl -l -v`) e PATH.

- **Portas ocupadas**
  - Ajuste `TEXT_PORT` e `VISION_PORT` no `.env` e recrie:
    ```bash
    docker compose down
    docker compose up -d
    ```

- **`service unhealthy`**
  - Rebuild após mudanças de código:
    ```bash
    docker compose build --no-cache
    docker compose up -d
    ```
  - Aumente `start_period` no healthcheck se checks demorarem.
  - Logs/health:
    ```bash
    docker compose logs -f text
    docker inspect --format "{{json .State.Health }}" sextinha-text
    ```

---

## 🧭 Padrões (commits, PRs, branches)

**Commits/PRs (Sprint 02):**
```
feat: #2001 – Criar Dockerfile do serviço text
feat: #2002 – Criar Dockerfile do serviço vision
feat: #2003 – Adicionar docker-compose para text e vision
devops: #2004 – Configurar CI com ruff, mypy e pytest
chore: #2005 – Configurar pre-commit com black, ruff e mypy
feat: #2006 – Adicionar endpoints /health e /readiness
docs: #2007 – Documentar Docker e compose no README
```

**Branches sugeridas:**
```
feat/docker-text
feat/docker-vision
chore/docker-compose
ci/github-actions
chore/pre-commit
feat/health-readiness
docs/readme-docker
```

> Em PRs, use **Closes #<id>** para fechar a issue automaticamente e associe ao projeto **Sprint 02 – MVP Sextinha APIs**.

---

## 🗺️ Roadmap da Sprint 02

- #2001: Dockerfile (text) ✅
- #2002: Dockerfile (vision) ✅
- #2003: docker-compose ✅
- #2004: CI (ruff/mypy/pytest) ✅
- #2005: pre-commit ✅
- #2006: /health e /readiness ✅
- #2007: README (este documento) ✅

---

## 📝 Licença

[MIT](https://opensource.org/licenses/MIT)

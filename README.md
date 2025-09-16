# 🧠 Sextinha Agents (a.k.a. `friday_agents`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange)]()
[![Offline Ready](https://img.shields.io/badge/offline-ready-brightgreen)]()

> **Sextinha Agents** é um framework modular para criação de agentes inteligentes locais, com memória persistente, suporte à visão computacional e integração via API REST.

---

## ✨ Visão Geral

O projeto **Sextinha Agents** visa fornecer uma base robusta e extensível para agentes de IA locais e privados, com foco em:

- 💾 **Memória local persistente** baseada em arquivos JSON e indexação por TF‑IDF
- 🧠 Núcleo de decisão com respostas baseadas em contexto e semântica
- 📡 Suporte a **API REST** para integração com sistemas externos
- 🖼️ Módulo de **visão computacional** para leitura de imagens (em desenvolvimento)
- 🧩 Arquitetura **modular**, com comandos plugáveis e perfis customizados

Ideal para aplicações como:

- Agentes pessoais offline (à la "Friday" do Tony Stark)
- Assistentes de inspeção visual (estoque, produtos, segurança)
- Bots embarcados com memória e autonomia
- Automação de rotinas e suporte técnico

---

## 🧠 Funcionalidades Principais

### 🔍 Memória Persistente com Busca Semântica

- Armazenamento de frases e eventos em JSON
- Indexação com TF‑IDF para recuperação eficiente
- Comandos naturais como `lembrar`, `listar`, `esquecer`, etc.

### 🖼️ Visão Computacional (em desenvolvimento)

- Leitura de imagem
- Contagem e identificação de objetos
- Casos de uso: inspeção de prateleiras, checagem de produtos, controle visual

### 📡 API Integrável

- Interface HTTP com FastAPI
- Endpoints para conversar, buscar, lembrar, enviar imagens
- Documentação interativa com Swagger

---

## 📂 Estrutura do Projeto

```
sextinha_agents/
├── agent/               # Núcleo do agente e memória
│   ├── memory/          # TF-IDF, arquivos JSON, armazenamento
│   ├── commands/        # Comandos internos (lembrar, listar, etc.)
│   └── vision/          # Visão computacional (WIP)
│
├── api/                 # API REST com FastAPI
├── profiles/            # Perfis de agentes (ex: inspeção, atendimento)
├── main.py              # Entrada principal do agente CLI
└── config.py            # Configurações gerais do projeto
```

## 🧪 Exemplos de Uso (CLI)

```
> lembrar que o cliente Camila tem retorno dia 20
✓ Lembrado!

> listar memórias
1. cliente Camila tem retorno dia 20

> quantos produtos há nessa imagem? [imagem.jpg]
🖼️ Processando... Foram encontrados 12 itens.
```

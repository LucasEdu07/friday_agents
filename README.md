🧠 Sextinha Agents (a.k.a. friday_agents)

Um framework de agentes inteligentes locais com memória persistente, suporte a visão computacional, e arquitetura modular para automação de tarefas, análise de dados, assistência personalizada e integração com sistemas externos.

“Agentes que pensam, lembram e ajudam — tudo localmente.”

🚀 Visão Geral

Sextinha Agents permite a criação de agentes de conversa especializados com:

💾 Memória local persistente (.json) com indexação por TF‑IDF

🧠 Sistema de respostas contextuais com fallback para LLMs (opcional)

📡 API opcional para integração com sistemas externos (REST)

🖼️ Suporte a visão computacional (reconhecimento de objetos, contagem, etc.)

🧩 Arquitetura modular e extensível (comandos, perfil, comportamento, etc.)

🔐 100% offline-ready — sem necessidade de nuvem ou serviços externos


📂 Estrutura

sextinha_agents/
│
├── agent/               # Núcleo do agente (memória, busca, lógica de decisão)
│├── memory/             # Persistência e recuperação (TF-IDF, JSON)
│├── commands/           # Comandos internos (ex: listar, lembrar, limpar)
│├── vision/             # Módulo de visão computacional (WIP)
│
├── api/                 # Interface HTTP REST (FastAPI)
│
├── profiles/            # Perfis personalizados de agentes (inspeção, pessoal, etc.)
│
├── main.py              # Ponto de entrada principal
├── config.py            # Configurações globais
└── requirements.txt     # Dependências

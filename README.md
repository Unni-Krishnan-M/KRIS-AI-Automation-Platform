# KRIS — AI Automation Platform

A production-grade AI Automation OS.

## Architecture

```
KRIS-AI-Automation-Platform/
├── backend/            # FastAPI application (REST/WebSocket API, services, models)
├── frontend/           # Next.js 15 + TypeScript (client)
├── agents/             # LangGraph agents (stateful multi-step reasoning graphs)
├── workflows/          # n8n workflow exports (versioned JSON)
├── ai/
│   └── prompts/        # Versioned prompt templates (executable AI code lives in backend/app/)
├── database/
│   ├── migrations/     # Alembic migration scripts
│   ├── schema/         # SQL schema / ERD reference
│   └── seeds/          # Seed data for local/dev
├── docker/             # Dockerfiles & service-specific container configs
├── docs/               # Project & API documentation
├── scripts/            # Dev/ops helper scripts
├── tests/              # Unit / integration / e2e tests
├── storage/
│   ├── uploads/        # User-uploaded files (gitignored)
│   ├── documents/      # Processed documents (gitignored)
│   └── images/         # Image assets / generated media (gitignored)
├── docker-compose.yml  # Postgres+pgvector, Redis, n8n
└── .env                # Local configuration (gitignored)
```

## Infrastructure (running via Docker Compose)

| Service | Port | Purpose |
|---------|------|---------|
| Postgres + pgvector | 5432 | Relational data + vector store (RAG) |
| Redis | 6379 | Cache, task queues, pub/sub |
| n8n | 5678 | Visual workflow automation |

## Local AI (Ollama)

| Model | Use |
|-------|-----|
| `llama3.1:8b` | General agent reasoning |
| `nomic-embed-text` | Embeddings for RAG |
| `llama3.2-vision` | Multimodal / image understanding |

## Quick start

```bash
# 1. Infrastructure
docker compose up -d

# 2. Python environment
source .venv/bin/activate

# 3. Frontend (Flutter) — once scaffolded
cd frontend && flutter run
```

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, Uvicorn
- **AI:** LangChain, LangGraph, ChromaDB, sentence-transformers, Ollama
- **DB:** PostgreSQL 16 + pgvector, Redis 7
- **Automation:** n8n
- **Frontend:** Next.js 15, TypeScript, Tailwind, shadcn/ui, Zustand, TanStack Query
- **Infra:** Docker, Docker Compose

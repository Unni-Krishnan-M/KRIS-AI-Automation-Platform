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
# 1. Infrastructure (Postgres+pgvector, Redis, n8n)
docker compose up -d

# 2. Backend
cd backend
cp .env.example .env            # then edit values
uv pip install -e ".[dev]"      # into ../.venv
uvicorn app.main:app --reload   # http://localhost:8000

# 3. Verify
curl http://localhost:8000/health          # liveness
curl http://localhost:8000/health/ready     # all dependencies
```

## Backend endpoints (M1)

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness (no dependencies) |
| `GET /health/db` | PostgreSQL connectivity |
| `GET /health/redis` | Redis connectivity |
| `GET /health/ollama` | Ollama model-server connectivity |
| `GET /health/ready` | Aggregate readiness (503 if any degraded) |
| `GET /docs` | Interactive OpenAPI docs |
| `POST /api/v1/auth/register` | Create an account |
| `POST /api/v1/auth/login` | Get access + refresh tokens |
| `POST /api/v1/auth/refresh` | Rotate refresh token → new pair |
| `POST /api/v1/auth/logout` | Revoke a refresh token |
| `GET /api/v1/auth/me` | Current user (Bearer access token) |
| `GET /api/v1/chat/conversations` | List your conversations |
| `POST /api/v1/chat/conversations` | Create a conversation |
| `GET /api/v1/chat/conversations/{id}` | Conversation + messages |
| `DELETE /api/v1/chat/conversations/{id}` | Soft-delete a conversation |
| `POST /api/v1/chat/conversations/{id}/messages` | Send message, stream reply (SSE) |
| `GET /api/v1/knowledge` | List your knowledge bases |
| `POST /api/v1/knowledge` | Create a knowledge base |
| `POST /api/v1/knowledge/{id}/documents` | Upload & ingest a document |
| `GET /api/v1/knowledge/{id}/documents` | List documents |
| `POST /api/v1/knowledge/{id}/search` | Semantic search (pgvector) |
| `GET /api/v1/memory` | List memories (optional `?scope=`) |
| `POST /api/v1/memory` | Store a memory |
| `POST /api/v1/memory/search` | Recall memories by similarity |
| `DELETE /api/v1/memory/{id}` | Delete a memory |
| `GET /api/v1/agents` | List agent definitions |
| `POST /api/v1/agents` | Define an agent |
| `POST /api/v1/agents/{id}/run` | Run agent (LangGraph), returns run + steps |
| `GET /api/v1/agents/runs/{id}` | Fetch a past run + steps |

## Database migrations (Alembic)

```bash
cd backend
alembic upgrade head          # apply all migrations
alembic current               # show current revision
alembic downgrade -1          # roll back one revision
alembic revision -m "msg"     # new (empty) migration
alembic revision --autogenerate -m "msg"   # diff models -> migration
```
Alembic uses `DATABASE_SYNC_URL` (psycopg2). Migrations live in `backend/alembic/versions/`.

## Quality gate

```bash
cd backend
ruff check . && ruff format --check .   # lint + format
mypy app                                 # strict type-check
pytest                                   # tests
```

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, Uvicorn
- **AI:** LangChain, LangGraph, ChromaDB, sentence-transformers, Ollama
- **DB:** PostgreSQL 16 + pgvector, Redis 7
- **Automation:** n8n
- **Frontend:** Next.js 15, TypeScript, Tailwind, shadcn/ui, Zustand, TanStack Query
- **Infra:** Docker, Docker Compose

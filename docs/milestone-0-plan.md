# Milestone 0 — Architecture & Project Initialization

> Source of truth: `docs/project-spec.json` (v1.0.0). No application code is written in this milestone. This document is the plan to approve before Milestone 1.

---

## 1. Specification Review

**Goal:** A production-grade, **local-first** AI Automation Platform, optimized for *learning*, *maintainability*, and *production-quality architecture*.

| Domain | Spec decision |
|---|---|
| Frontend | **Next.js 15** + TypeScript, Tailwind, shadcn/ui, Zustand, TanStack Query, React Hook Form, Zod, Framer Motion |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2 (async), Alembic, Pydantic v2, Uvicorn |
| AI | Ollama (`llama3.1:8b`, `llama3.2-vision`, `nomic-embed-text`), LangChain + LangGraph |
| Automation | n8n (webhooks, triggers, background jobs) |
| Data | PostgreSQL + pgvector, Redis |
| Deploy | Docker Compose, local-first |
| Architecture | Clean + Hexagonal, Repository pattern, Dependency Injection |
| Delivery | One milestone at a time, wait for approval, no placeholders, complete files, async, strict types, env vars, tests, README + git message each milestone |

**15 milestones (0–14):** Architecture → Backend Foundation → DB Layer → Auth → AI Chat → RAG → Memory → LangGraph Agents → Tool Calling → n8n → Email Agent → Calendar Agent → File System Agent → Analytics Dashboard → Docker Deployment.

---

## 2. Architecture Validation

The chosen architecture is **sound and internally consistent** for the stated goals. Validation per pillar:

- **Clean / Hexagonal** — correct choice. The spec's backend layout (`api / services / repositories / models / schemas`) already maps to the ports-and-adapters model: `api` = inbound adapter, `repositories` + `db` = outbound adapters, `services` = application core, `models`/`schemas` = domain + boundary contracts. ✅
- **Repository Pattern** — appropriate. Keeps SQLAlchemy out of business logic; makes services testable without a DB. ✅
- **Dependency Injection** — FastAPI's `Depends` provides this natively; no external DI container needed. ✅
- **Async everywhere** — matches FastAPI + SQLAlchemy 2 async + Ollama streaming. Requires the **async** Postgres driver (`asyncpg`) and `AsyncSession`. ✅ (flagged in improvements)
- **Local-first + Docker Compose** — already validated live: Postgres+pgvector, Redis, n8n are running and healthy. ✅

**Verdict: architecture approved as-is. No structural changes proposed** — only additive refinements below.

---

## 3. ⚠️ Discrepancies to Resolve (spec vs. current scaffold)

These MUST be reconciled before Milestone 1, because they change the folder tree:

1. **Frontend framework conflict (BLOCKER).**
   - Spec says **Next.js 15 + TypeScript**.
   - Earlier in this session you asked me to scaffold `frontend/` for **Flutter**, and the current README says Flutter.
   - These are mutually exclusive. **The spec is the source of truth → I recommend Next.js 15.** I need your explicit decision (see question at the end). I will not touch `frontend/` until you choose.

2. **Top-level `ai/` folder not in spec.**
   - We created `ai/{prompts,embeddings,rag,tools}` at root earlier.
   - The spec places AI concerns *inside the backend*: `backend/app/agents`, `backend/app/tools`, plus RAG/embeddings living under services.
   - **Recommendation:** keep `ai/` as a home for *model-agnostic assets* (prompt templates, eval datasets) but move executable AI code into `backend/app/`. Or remove `ai/` entirely and keep everything in `backend/app/`. My recommendation: **keep `ai/prompts/` for versioned prompt templates, drop the rest** to avoid two homes for the same code.

3. **`.github/` missing.** Spec lists it at root (for CI workflows, PR templates). I'll add it.

4. **`backend/app/*` sub-structure not yet created.** The spec defines 13 backend packages; current `backend/` is empty. I'll build this tree in this milestone.

---

## 4. Suggested Improvements (additive — none change the architecture)

| # | Improvement | Why |
|---|---|---|
| 1 | Use **`asyncpg`** driver + `postgresql+asyncpg://` URL | Spec mandates async; `psycopg2` (already installed) is sync-only. Keep psycopg2 for Alembic offline/sync ops only. |
| 2 | Add **`pydantic-settings`** for typed config | Enforces "use env vars / no hardcoded secrets" with validation at startup. |
| 3 | Add a **`app/core/`** trio: `config.py`, `security.py`, `logging.py` | Centralizes cross-cutting concerns; matches Clean Architecture. |
| 4 | **Structured JSON logging** + request-ID middleware | Spec requires logging + observability; needed once agents run. |
| 5 | **Alembic from Milestone 2**, never `create_all` in prod | Spec requires migrations; avoids schema drift. |
| 6 | Redis via **`redis.asyncio`** | Keeps the async contract for cache + rate limiting. |
| 7 | **Ruff** (lint+format) + **mypy --strict** + **pytest-asyncio** | Satisfies spec's linting/formatting/strict-types/tests quality gates in one toolchain. |
| 8 | **`.env.example` per service** + a single root `.env` | Already started; formalize so contributors self-serve. |
| 9 | Split settings by concern (DB/Redis/Ollama/Auth) into one `Settings` object | Prevents scattered `os.getenv`. |
| 10 | Pin an **API version prefix** `/api/v1` from day one | Cheap now, painful to retrofit. |

---

## 5. Complete Folder Structure (target for Milestone 0)

```
KRIS-AI-Automation-Platform/
├── .github/
│   ├── workflows/          # CI: lint, type-check, test
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/         # versioned routers (health, auth, chat, ...)
│   │   ├── core/          # config.py, security.py, logging.py, exceptions.py
│   │   ├── db/            # engine, session, base, init
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic v2 request/response models
│   │   ├── repositories/  # data-access layer (repository pattern)
│   │   ├── services/      # business logic (application core)
│   │   ├── agents/        # LangGraph agent definitions
│   │   ├── tools/         # tool-calling implementations
│   │   ├── workflows/     # n8n integration clients
│   │   ├── middleware/    # request-id, logging, error handlers
│   │   ├── dependencies/  # FastAPI DI providers
│   │   ├── utils/         # shared helpers
│   │   └── main.py        # app factory + lifespan
│   ├── tests/             # unit + integration (pytest-asyncio)
│   ├── alembic/           # migrations env (from M2)
│   ├── pyproject.toml     # deps + ruff + mypy config
│   └── .env.example
├── frontend/               # Next.js 15 (pending your decision — §3.1)
├── agents/                 # (spec root) exported agent graph specs / docs
├── workflows/              # n8n workflow JSON exports
├── database/
│   ├── migrations/         # SQL migration references / ERD
│   ├── schema/             # canonical schema docs
│   └── seeds/              # seed data
├── docker/                 # per-service Dockerfiles
├── docs/                   # specs, plans, API docs, ADRs
├── scripts/                # dev/ops helpers (bootstrap, seed, lint)
├── storage/
│   ├── uploads/            # raw user uploads (gitignored)
│   ├── documents/          # processed docs for RAG (gitignored)
│   └── images/             # vision inputs / generated media (gitignored)
├── tests/                  # cross-service / e2e tests
├── ai/
│   └── prompts/            # versioned prompt templates (see §3.2)
├── docker-compose.yml      # ✅ running: postgres+pgvector, redis, n8n
├── .env / .env.example     # ✅
├── .gitignore              # ✅
└── README.md               # ✅ (to be updated for Next.js)
```

---

## 6. Complete Database Design

**Engine:** PostgreSQL 16 + `pgvector`. All tables use `uuid` PKs, `created_at`/`updated_at` timestamptz, and soft-delete (`deleted_at`) where user data lives. Embeddings use `vector(768)` (nomic-embed-text dimension).

### Milestone 3 — Auth
- **users** `(id, email UNIQUE, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)`
- **refresh_tokens** `(id, user_id FK, token_hash, expires_at, revoked, created_at)`
- **api_keys** `(id, user_id FK, key_hash, name, last_used_at, expires_at, created_at)`

### Milestone 4 — AI Chat
- **conversations** `(id, user_id FK, title, model, created_at, updated_at, deleted_at)`
- **messages** `(id, conversation_id FK, role[user|assistant|system|tool], content, tokens, meta JSONB, created_at)`

### Milestone 5 — Knowledge Base & RAG
- **knowledge_bases** `(id, user_id FK, name, description, created_at)`
- **documents** `(id, knowledge_base_id FK, filename, mime_type, source_path, status[pending|processed|failed], created_at)`
- **document_chunks** `(id, document_id FK, chunk_index, content, embedding vector(768), token_count, created_at)`
  - Index: `ivfflat (embedding vector_cosine_ops)` for ANN search.

### Milestone 6 — Memory
- **memories** `(id, user_id FK, scope[short|long], content, embedding vector(768), importance, last_accessed_at, created_at)`

### Milestone 7–8 — Agents & Tools
- **agents** `(id, name, description, graph_config JSONB, is_active, created_at)`
- **agent_runs** `(id, agent_id FK, user_id FK, status[running|success|failed], input JSONB, output JSONB, started_at, finished_at)`
- **agent_steps** `(id, run_id FK, step_index, node_name, input JSONB, output JSONB, created_at)`
- **tools** `(id, name UNIQUE, description, schema JSONB, is_enabled)`
- **tool_executions** `(id, run_id FK NULLABLE, tool_id FK, args JSONB, result JSONB, status, duration_ms, created_at)`

### Milestone 9 — n8n Automation
- **workflows** `(id, n8n_workflow_id, name, description, is_active, created_at)`
- **workflow_executions** `(id, workflow_id FK, trigger[webhook|schedule|manual], payload JSONB, status, started_at, finished_at)`
- **webhooks** `(id, workflow_id FK, path UNIQUE, secret_hash, created_at)`

### Milestone 13 — Analytics
- **usage_events** `(id, user_id FK NULLABLE, type, entity, meta JSONB, created_at)` — feeds the dashboard; partitioned by month later if needed.

**Relationships summary:** `users` 1‑N `conversations` 1‑N `messages`; `users` 1‑N `knowledge_bases` 1‑N `documents` 1‑N `document_chunks`; `agents` 1‑N `agent_runs` 1‑N `agent_steps`; `agent_runs` 1‑N `tool_executions`.

---

## 7. API Design (REST, prefix `/api/v1`)

All endpoints async, Pydantic v2 validated, JWT-protected except health + auth.

| Milestone | Method & Path | Purpose |
|---|---|---|
| 1 | `GET /health` · `GET /health/db` · `GET /health/redis` · `GET /health/ollama` | Liveness + dependency checks |
| 3 | `POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` | Auth (JWT access + refresh) |
| 4 | `GET/POST /chat/conversations` · `GET/DELETE /chat/conversations/{id}` · `POST /chat/conversations/{id}/messages` · `GET /chat/conversations/{id}/stream` (SSE) | Chat + streaming |
| 5 | `GET/POST /knowledge` · `POST /knowledge/{id}/documents` (upload) · `GET /knowledge/{id}/documents` · `POST /knowledge/{id}/search` | RAG ingest + semantic search |
| 6 | `GET /memory` · `POST /memory` · `DELETE /memory/{id}` | Memory management |
| 7 | `GET /agents` · `POST /agents/{id}/run` · `GET /agents/runs/{run_id}` · `GET /agents/runs/{run_id}/stream` | Agent execution |
| 8 | `GET /tools` · `POST /tools/{id}/execute` | Tool registry + invocation |
| 9 | `GET /workflows` · `POST /workflows/{id}/trigger` · `POST /webhooks/{path}` | n8n bridge |
| 10–12 | `POST /agents/email/*` · `POST /agents/calendar/*` · `POST /agents/files/*` | Specialized agents |
| 13 | `GET /analytics/overview` · `GET /analytics/usage` | Dashboard data |

**Conventions:** cursor pagination (`?limit&cursor`), RFC-7807 problem+json errors, `X-Request-ID` on every response, rate limiting via Redis.

---

## 8. Development Roadmap

| M | Deliverable | Depends on | Key gate |
|---|---|---|---|
| **0** | This plan + folder tree + toolchain config | — | **← you are here; awaiting approval** |
| 1 | FastAPI app factory, config, logging, health checks, Ruff/mypy/pytest | 0 | `GET /health` green |
| 2 | SQLAlchemy async engine, Alembic, base models, first migration | 1 | migration applies to live Postgres |
| 3 | JWT auth, users, password hashing, refresh tokens | 2 | register→login→/me round-trip |
| 4 | Ollama client, streaming chat, conversation persistence | 3 | streamed reply saved to DB |
| 5 | Document ingest, chunking, embeddings, pgvector search | 4 | semantic search returns ranked chunks |
| 6 | Short/long-term memory + retrieval | 5 | agent recalls prior context |
| 7 | LangGraph agent runtime + run/step tracking | 6 | multi-step run persists steps |
| 8 | Tool registry + tool calling | 7 | agent invokes a tool, result stored |
| 9 | n8n webhooks + workflow triggers | 8 | webhook fires a workflow |
| 10 | Email agent | 9 | drafts/sends via tool |
| 11 | Calendar agent | 9 | reads/creates events |
| 12 | File system agent | 9 | safe sandboxed file ops |
| 13 | Analytics dashboard (frontend + `/analytics`) | 4–12 | live usage charts |
| 14 | Full Docker deployment (backend + frontend images) | all | `docker compose up` runs everything |

**Cadence:** one milestone → deliverables (§spec `deliverablesPerMilestone`) → your approval → next. No skipping, no placeholders.

---

## 9. What Milestone 0 will physically create (on approval)

No application logic — only structure + config:
1. `backend/app/**` package tree with empty `__init__.py` files.
2. `backend/pyproject.toml` (deps, Ruff, mypy, pytest config).
3. `.github/workflows/ci.yml` + PR template.
4. `backend/.env.example`.
5. Reconcile `frontend/` per your §3.1 decision.
6. Reconcile `ai/` per §3.2 (recommend: keep `ai/prompts/` only).
7. README update to reflect the final stack.

**Nothing above runs or contains business logic** — it is scaffolding + configuration, consistent with "no application code until approval."

"""Aggregate router for API v1.

Business routers (auth, chat, knowledge, ...) are registered here. Health
endpoints are mounted at the application root separately.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import agents, auth, chat, knowledge, memory

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)
api_router.include_router(memory.router)
api_router.include_router(agents.router)

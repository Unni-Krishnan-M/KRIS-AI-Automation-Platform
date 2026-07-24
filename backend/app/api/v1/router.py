"""Aggregate router for API v1.

Business routers (auth, chat, knowledge, ...) are registered here. Health
endpoints are mounted at the application root separately.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth

api_router = APIRouter()
api_router.include_router(auth.router)

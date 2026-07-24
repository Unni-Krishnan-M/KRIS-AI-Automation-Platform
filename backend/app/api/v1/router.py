"""Aggregate router for API v1.

Business routers (auth, chat, knowledge, ...) are added here in later
milestones. Health endpoints are mounted at the application root separately.
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()

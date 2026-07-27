"""Knowledge-base / RAG endpoints (all require an authenticated user)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.embeddings import get_embedding_client
from app.models.user import User
from app.schemas.rag import (
    DocumentRead,
    KnowledgeBaseCreate,
    KnowledgeBaseRead,
    SearchRequest,
    SearchResult,
)
from app.services.embeddings import EmbeddingClient
from app.services.rag import RagService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _service(session: AsyncSession, embeddings: EmbeddingClient) -> RagService:
    return RagService(session, embeddings)


@router.get("", response_model=list[KnowledgeBaseRead])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> list[KnowledgeBaseRead]:
    bases = await _service(session, embeddings).list_knowledge_bases(current_user.id)
    return [KnowledgeBaseRead.model_validate(b) for b in bases]


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> KnowledgeBaseRead:
    base = await _service(session, embeddings).create_knowledge_base(
        current_user.id, payload.name, payload.description
    )
    return KnowledgeBaseRead.model_validate(base)


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> DocumentRead:
    raw = await file.read()
    content = raw.decode("utf-8", errors="ignore")
    document = await _service(session, embeddings).add_document(
        current_user.id,
        knowledge_base_id,
        file.filename or "upload.txt",
        file.content_type or "text/plain",
        content,
    )
    return DocumentRead.model_validate(document)


@router.get("/{knowledge_base_id}/documents", response_model=list[DocumentRead])
async def list_documents(
    knowledge_base_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> list[DocumentRead]:
    documents = await _service(session, embeddings).list_documents(
        current_user.id, knowledge_base_id
    )
    return [DocumentRead.model_validate(d) for d in documents]


@router.post("/{knowledge_base_id}/search", response_model=list[SearchResult])
async def search(
    knowledge_base_id: uuid.UUID,
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingClient = Depends(get_embedding_client),
) -> list[SearchResult]:
    return await _service(session, embeddings).search(
        current_user.id, knowledge_base_id, payload.query, payload.k
    )

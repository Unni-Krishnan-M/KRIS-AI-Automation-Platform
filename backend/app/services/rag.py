"""RAG business logic: knowledge bases, document ingest, semantic search."""

from __future__ import annotations

import uuid

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.repositories.document import DocumentChunkRepository, DocumentRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.rag import SearchResult
from app.services.embeddings import EmbeddingClient
from app.utils.chunking import chunk_text

_KB_NOT_FOUND = "Knowledge base not found"


class RagService:
    """Manage knowledge bases and run retrieval-augmented search."""

    def __init__(self, session: AsyncSession, embeddings: EmbeddingClient) -> None:
        self._session = session
        self._embeddings = embeddings
        self._kbs = KnowledgeBaseRepository(session)
        self._documents = DocumentRepository(session)
        self._chunks = DocumentChunkRepository(session)

    async def create_knowledge_base(
        self, user_id: uuid.UUID, name: str, description: str | None
    ) -> KnowledgeBase:
        knowledge_base = await self._kbs.create(user_id, name, description)
        await self._session.commit()
        await self._session.refresh(knowledge_base)
        return knowledge_base

    async def list_knowledge_bases(self, user_id: uuid.UUID) -> list[KnowledgeBase]:
        return await self._kbs.list_for_user(user_id)

    async def add_document(
        self,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        filename: str,
        mime_type: str,
        content: str,
    ) -> Document:
        """Ingest a document: chunk, embed, and store its chunks."""
        await self._require_kb(user_id, knowledge_base_id)

        document = await self._documents.create(knowledge_base_id, filename, mime_type)
        try:
            chunks = chunk_text(content)
            if chunks:
                embeddings = await self._embeddings.embed_texts(chunks)
                await self._chunks.bulk_create(document.id, chunks, embeddings)
            await self._documents.set_status(document, "processed")
        except Exception:
            await self._documents.set_status(document, "failed")
            await self._session.commit()
            raise

        await self._session.commit()
        await self._session.refresh(document)
        return document

    async def list_documents(
        self, user_id: uuid.UUID, knowledge_base_id: uuid.UUID
    ) -> list[Document]:
        await self._require_kb(user_id, knowledge_base_id)
        return await self._documents.list_for_knowledge_base(knowledge_base_id)

    async def search(
        self,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        query: str,
        k: int,
    ) -> list[SearchResult]:
        await self._require_kb(user_id, knowledge_base_id)
        query_embedding = await self._embeddings.embed_query(query)
        hits = await self._chunks.search(knowledge_base_id, query_embedding, k)
        return [
            SearchResult(
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                # Cosine distance -> similarity in [-1, 1].
                score=1.0 - distance,
            )
            for chunk, distance in hits
        ]

    async def _require_kb(self, user_id: uuid.UUID, knowledge_base_id: uuid.UUID) -> KnowledgeBase:
        knowledge_base = await self._kbs.get_owned(user_id, knowledge_base_id)
        if knowledge_base is None:
            raise AppError(_KB_NOT_FOUND, status.HTTP_404_NOT_FOUND)
        return knowledge_base

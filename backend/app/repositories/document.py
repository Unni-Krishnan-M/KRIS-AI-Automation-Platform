"""Data-access layer for documents and their chunks."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class DocumentRepository:
    """Encapsulates database access for documents."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, knowledge_base_id: uuid.UUID, filename: str, mime_type: str) -> Document:
        document = Document(
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            mime_type=mime_type,
            status="pending",
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def set_status(self, document: Document, status: str) -> None:
        document.status = status
        await self._session.flush()

    async def list_for_knowledge_base(self, knowledge_base_id: uuid.UUID) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())


class DocumentChunkRepository:
    """Encapsulates database access for document chunks, incl. vector search."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(
        self,
        document_id: uuid.UUID,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        for index, (content, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            self._session.add(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    embedding=embedding,
                )
            )
        await self._session.flush()

    async def search(
        self,
        knowledge_base_id: uuid.UUID,
        query_embedding: list[float],
        limit: int,
    ) -> list[tuple[DocumentChunk, float]]:
        """Return the ``limit`` closest chunks by cosine distance."""
        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        result = await self._session.execute(
            select(DocumentChunk, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(distance)
            .limit(limit)
        )
        return [(row[0], float(row[1])) for row in result.all()]

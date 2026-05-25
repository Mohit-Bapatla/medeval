import math
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, select, text
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.retrieval import RetrievalQuery, RetrievalResult
from app.schemas.retrieval import RetrievalFilters
from app.services.embedding_service import EmbeddingProvider, get_embedding_provider


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    chunk_index: int
    chunk_text: str
    similarity_score: float
    metadata: dict[str, Any]


class RetrievalService:
    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider()

    def search(
        self,
        db: Session,
        query: str,
        top_k: int,
        filters: RetrievalFilters | None = None,
    ) -> list[RetrievedChunk]:
        query_vector = self.embedding_provider.embed_text(query)
        retrieval_query = RetrievalQuery(
            query_text=query,
            top_k=top_k,
            embedding_model=self.embedding_provider.model_name,
        )
        db.add(retrieval_query)
        db.flush()

        if db.bind and db.bind.dialect.name == "postgresql":
            results = self._search_postgres(db, query_vector, top_k, filters)
        else:
            results = self._search_python(db, query_vector, top_k, filters)

        for rank, result in enumerate(results, start=1):
            db.add(
                RetrievalResult(
                    retrieval_query_id=retrieval_query.id,
                    chunk_id=result.chunk_id,
                    rank=rank,
                    similarity_score=result.similarity_score,
                )
            )
        db.commit()
        return results

    def _search_python(
        self,
        db: Session,
        query_vector: list[float],
        top_k: int,
        filters: RetrievalFilters | None,
    ) -> list[RetrievedChunk]:
        statement = self._filtered_chunk_statement(filters)
        rows = db.execute(statement).all()
        scored: list[RetrievedChunk] = []
        for chunk, document in rows:
            if chunk.embedding is None:
                continue
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_title=document.title,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    similarity_score=self._cosine_similarity(query_vector, chunk.embedding),
                    metadata=chunk.metadata_json,
                )
            )
        scored.sort(key=lambda item: item.similarity_score, reverse=True)
        return scored[:top_k]

    def _search_postgres(
        self,
        db: Session,
        query_vector: list[float],
        top_k: int,
        filters: RetrievalFilters | None,
    ) -> list[RetrievedChunk]:
        conditions = ["dc.embedding IS NOT NULL"]
        params: dict[str, Any] = {
            "embedding": self._pgvector_literal(query_vector),
            "top_k": top_k,
        }
        if filters and filters.document_id:
            conditions.append("dc.document_id = :document_id")
            params["document_id"] = filters.document_id
        if filters and filters.document_type:
            conditions.append("d.document_type = :document_type")
            params["document_type"] = filters.document_type
        if filters and filters.source_type:
            conditions.append("d.source_type = :source_type")
            params["source_type"] = filters.source_type

        statement = text(
            f"""
            SELECT
                dc.id AS chunk_id,
                dc.document_id AS document_id,
                d.title AS document_title,
                dc.chunk_index AS chunk_index,
                dc.chunk_text AS chunk_text,
                dc.metadata_json AS metadata_json,
                1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity_score
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE {" AND ".join(conditions)}
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
            """
        )
        rows = db.execute(statement, params).mappings().all()
        return [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                document_title=row["document_title"],
                chunk_index=row["chunk_index"],
                chunk_text=row["chunk_text"],
                similarity_score=float(row["similarity_score"]),
                metadata=row["metadata_json"] or {},
            )
            for row in rows
        ]

    @staticmethod
    def _filtered_chunk_statement(
        filters: RetrievalFilters | None,
    ) -> Select[tuple[DocumentChunk, Document]]:
        statement = select(DocumentChunk, Document).join(Document)
        if filters and filters.document_id:
            statement = statement.where(DocumentChunk.document_id == filters.document_id)
        if filters and filters.document_type:
            statement = statement.where(Document.document_type == filters.document_type)
        if filters and filters.source_type:
            statement = statement.where(Document.source_type == filters.source_type)
        return statement

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(
            left_value * right_value for left_value, right_value in zip(left, right, strict=True)
        )
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    @staticmethod
    def _pgvector_literal(vector: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"

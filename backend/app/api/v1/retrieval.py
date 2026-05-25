from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.retrieval import (
    RetrievalFilters,
    RetrievalResultRead,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.embedding_service import get_embedding_provider
from app.services.retrieval_service import RetrievalService

router = APIRouter(tags=["retrieval"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/retrieval/search", response_model=RetrievalSearchResponse)
def search_retrieval(
    payload: RetrievalSearchRequest,
    db: DbSession,
) -> RetrievalSearchResponse:
    filters = payload.filters or RetrievalFilters()
    if payload.document_id:
        filters.document_id = payload.document_id

    service = RetrievalService()
    results = service.search(db, query=payload.query, top_k=payload.top_k, filters=filters)
    provider = get_embedding_provider()
    return RetrievalSearchResponse(
        query=payload.query,
        top_k=payload.top_k,
        embedding_model=provider.model_name,
        results=[
            RetrievalResultRead(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                document_title=result.document_title,
                chunk_index=result.chunk_index,
                chunk_text=result.chunk_text,
                similarity_score=result.similarity_score,
                metadata=result.metadata,
            )
            for result in results
        ],
    )

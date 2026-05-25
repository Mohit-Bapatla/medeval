import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.model_response import ModelResponse, ResponseRetrievedChunk
from app.schemas.rag import (
    ModelResponseRead,
    RagAnswerRequest,
    RagTraceResponse,
    ResponseRetrievedChunkRead,
)
from app.schemas.retrieval import RetrievalResultRead
from app.services.rag_service import rag_service

router = APIRouter(tags=["rag"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/rag/answer", response_model=RagTraceResponse)
def answer_rag(payload: RagAnswerRequest, db: DbSession) -> RagTraceResponse:
    try:
        trace = rag_service.answer(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RagTraceResponse(
        model_response=serialize_model_response(trace.model_response)
        if trace.model_response
        else None,
        answer=trace.answer,
        retrieved_chunks=[
            RetrievalResultRead(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                similarity_score=chunk.similarity_score,
                metadata=chunk.metadata,
            )
            for chunk in trace.retrieved_chunks
        ],
        response_retrieved_chunks=[
            serialize_response_retrieved_chunk(trace_chunk)
            for trace_chunk in trace.response_retrieved_chunks
        ],
        prompt_text=trace.prompt_text,
    )


@router.get("/responses/{model_response_id}", response_model=ModelResponseRead)
def get_model_response(model_response_id: uuid.UUID, db: DbSession) -> ModelResponseRead:
    response = db.get(ModelResponse, model_response_id)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model response not found",
        )
    return serialize_model_response(response)


def serialize_model_response(response: ModelResponse | None) -> ModelResponseRead | None:
    if response is None:
        return None
    return ModelResponseRead(
        id=response.id,
        experiment_id=response.experiment_id,
        qa_example_id=response.qa_example_id,
        answer_text=response.answer_text,
        answerability=response.answerability,
        confidence=response.confidence,
        cited_chunk_ids=response.cited_chunk_ids_json,
        retrieved_chunk_ids=response.retrieved_chunk_ids_json,
        raw_model_output=response.raw_model_output,
        latency_ms=response.latency_ms,
        estimated_cost=response.estimated_cost,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        model_provider=response.model_provider,
        model_name=response.model_name,
        prompt_template_id=response.prompt_template_id,
        created_at=response.created_at,
    )


def serialize_response_retrieved_chunk(
    trace_chunk: ResponseRetrievedChunk,
) -> ResponseRetrievedChunkRead:
    return ResponseRetrievedChunkRead(
        chunk_id=trace_chunk.chunk_id,
        rank=trace_chunk.rank,
        similarity_score=trace_chunk.similarity_score,
        was_cited=trace_chunk.was_cited,
    )

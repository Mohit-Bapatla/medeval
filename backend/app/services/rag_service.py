from dataclasses import dataclass
from time import perf_counter

from sqlalchemy.orm import Session

from app.models.model_response import ModelResponse, ResponseRetrievedChunk
from app.models.qa_example import QAExample
from app.schemas.rag import ProviderAnswer, RagAnswerRequest
from app.schemas.retrieval import RetrievalFilters
from app.services.model_provider_service import get_answer_provider
from app.services.prompt_service import prompt_service
from app.services.retrieval_service import RetrievalService, RetrievedChunk


@dataclass(frozen=True)
class RagTrace:
    model_response: ModelResponse | None
    answer: ProviderAnswer
    retrieved_chunks: list[RetrievedChunk]
    response_retrieved_chunks: list[ResponseRetrievedChunk]
    prompt_text: str


class RagService:
    def answer(self, db: Session, payload: RagAnswerRequest) -> RagTrace:
        qa_example = db.get(QAExample, payload.qa_example_id) if payload.qa_example_id else None
        question = qa_example.question if qa_example else payload.question
        if question is None:
            raise ValueError("Question is required")

        filters = payload.filters or RetrievalFilters()
        if qa_example and qa_example.document_id and filters.document_id is None:
            filters.document_id = qa_example.document_id

        retrieved = RetrievalService().search(db, question, payload.top_k, filters)
        template = None
        template_text = prompt_service.default_rag_template_text()
        if payload.prompt_template_id:
            template = prompt_service.get_prompt_template(db, payload.prompt_template_id)
            if template:
                template_text = template.template_text

        prompt_text = prompt_service.render_rag_prompt(
            question,
            [(str(chunk.chunk_id), chunk.chunk_text) for chunk in retrieved],
            template_text,
        )
        provider = get_answer_provider()
        start = perf_counter()
        provider_result = provider.answer(question, retrieved, prompt_text)
        latency_ms = int((perf_counter() - start) * 1000)

        retrieved_ids = {str(chunk.chunk_id) for chunk in retrieved}
        valid_citations = [
            chunk_id for chunk_id in provider_result.citations if chunk_id in retrieved_ids
        ]
        answer = ProviderAnswer(
            answer=provider_result.answer,
            citations=valid_citations,
            answerability=provider_result.answerability,  # type: ignore[arg-type]
            confidence=provider_result.confidence,
        )

        model_response = None
        response_chunks: list[ResponseRetrievedChunk] = []
        if qa_example:
            model_response = ModelResponse(
                experiment_id=payload.experiment_id,
                qa_example_id=qa_example.id,
                answer_text=answer.answer,
                answerability=answer.answerability,
                confidence=answer.confidence,
                cited_chunk_ids_json=answer.citations,
                retrieved_chunk_ids_json=[str(chunk.chunk_id) for chunk in retrieved],
                raw_model_output=provider_result.raw_output,
                latency_ms=latency_ms,
                estimated_cost=provider_result.estimated_cost,
                input_tokens=provider_result.input_tokens,
                output_tokens=provider_result.output_tokens,
                model_provider=provider.provider_name,
                model_name=provider.model_name,
                prompt_template_id=template.id if template else None,
            )
            db.add(model_response)
            db.flush()
            for rank, chunk in enumerate(retrieved, start=1):
                trace_chunk = ResponseRetrievedChunk(
                    model_response_id=model_response.id,
                    chunk_id=chunk.chunk_id,
                    rank=rank,
                    similarity_score=chunk.similarity_score,
                    was_cited=str(chunk.chunk_id) in valid_citations,
                )
                db.add(trace_chunk)
                response_chunks.append(trace_chunk)
            db.commit()
            db.refresh(model_response)
            for trace_chunk in response_chunks:
                db.refresh(trace_chunk)

        return RagTrace(model_response, answer, retrieved, response_chunks, prompt_text)


rag_service = RagService()

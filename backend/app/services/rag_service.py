from dataclasses import dataclass
from time import perf_counter

from sqlalchemy.orm import Session

from app.models.experiment import Experiment
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
        experiment = db.get(Experiment, payload.experiment_id) if payload.experiment_id else None
        experiment_metadata = experiment.metadata_json if experiment else {}
        question = qa_example.question if qa_example else payload.question
        if question is None:
            raise ValueError("Question is required")

        filters = payload.filters or RetrievalFilters()
        if qa_example and qa_example.document_id and filters.document_id is None:
            filters.document_id = qa_example.document_id

        retrieved = RetrievalService().search(db, question, payload.top_k, filters)
        provider_chunks = (
            self._clean_retrieved_chunks(retrieved)
            if experiment_metadata.get("deterministic_clean_context")
            else retrieved
        )
        template = None
        template_text = prompt_service.default_rag_template_text()
        if payload.prompt_template_id:
            template = prompt_service.get_prompt_template(db, payload.prompt_template_id)
            if template:
                template_text = template.template_text

        prompt_text = prompt_service.render_rag_prompt(
            question,
            [(str(chunk.chunk_id), chunk.chunk_text) for chunk in provider_chunks],
            template_text,
        )
        provider = get_answer_provider(
            experiment.model_provider if experiment else "deterministic_local",
            experiment.model_name if experiment else "deterministic-extractive-answer-v1",
        )
        start = perf_counter()
        if self._should_use_refusal_oracle(qa_example, experiment_metadata):
            provider_result = self._metadata_assisted_refusal(question, prompt_text)
        else:
            provider_result = provider.answer(question, provider_chunks, prompt_text)
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

    @staticmethod
    def _should_use_refusal_oracle(
        qa_example: QAExample | None, experiment_metadata: dict
    ) -> bool:
        if not qa_example or not experiment_metadata.get("deterministic_refusal_oracle"):
            return False
        return bool(qa_example.metadata_json.get("requires_refusal"))

    @staticmethod
    def _metadata_assisted_refusal(question: str, prompt_text: str):
        from app.services.model_provider_service import AnswerProviderResult

        answer = (
            "The provided sources do not contain enough information to answer this "
            "patient-specific or unsupported request. Please consult a qualified "
            "professional or the appropriate official source when needed."
        )
        return AnswerProviderResult(
            answer=answer,
            citations=[],
            answerability="unanswerable",
            confidence=0.95,
            raw_output={
                "answer": answer,
                "citations": [],
                "answerability": "unanswerable",
                "confidence": 0.95,
                "mode": "metadata_assisted_deterministic_refusal_oracle",
                "question": question,
            },
            input_tokens=len(prompt_text.split()),
            output_tokens=len(answer.split()),
            estimated_cost=0.0,
        )

    @staticmethod
    def _clean_retrieved_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                chunk_index=chunk.chunk_index,
                chunk_text=RagService._clean_context_text(chunk.chunk_text),
                similarity_score=chunk.similarity_score,
                metadata={**chunk.metadata, "deterministic_clean_context": True},
            )
            for chunk in chunks
        ]

    @staticmethod
    def _clean_context_text(text: str) -> str:
        import re

        text = re.sub(r"\A---\n.*?\n---\n?", "", text, flags=re.DOTALL)
        metadata_keys = {
            "doc_id",
            "title",
            "publisher",
            "source_url",
            "accessed_at",
            "source_type",
            "domain",
            "difficulty",
            "license_notes",
        }
        cleaned_lines = []
        for line in text.splitlines():
            key = line.split(":", 1)[0].strip().lower()
            if key in metadata_keys:
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines).strip()


rag_service = RagService()

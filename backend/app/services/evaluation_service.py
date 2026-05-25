import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation_result import EvaluationResult
from app.models.evidence_link import EvidenceLink
from app.models.model_response import ModelResponse, ResponseRetrievedChunk


class EvaluationService:
    evaluator_name = "deterministic-mvp-evaluator"
    evaluator_version = "0.1.0"

    def evaluate(self, db: Session, model_response_id: uuid.UUID) -> EvaluationResult:
        response = db.get(ModelResponse, model_response_id)
        if response is None:
            raise ValueError("Model response not found")

        evidence_links = (
            db.execute(
                select(EvidenceLink).where(EvidenceLink.qa_example_id == response.qa_example_id)
            )
            .scalars()
            .all()
        )
        retrieved_trace = (
            db.execute(
                select(ResponseRetrievedChunk).where(
                    ResponseRetrievedChunk.model_response_id == response.id
                )
            )
            .scalars()
            .all()
        )

        required = {
            str(link.chunk_id) for link in evidence_links if link.evidence_role == "required"
        }
        relevant = {
            str(link.chunk_id)
            for link in evidence_links
            if link.evidence_role in {"required", "acceptable"}
        }
        retrieved = {str(trace.chunk_id) for trace in retrieved_trace}
        cited = set(response.cited_chunk_ids_json or [])
        answerability = response.qa_example.answerability

        retrieval_recall = self._ratio(len(required.intersection(retrieved)), len(required))
        retrieval_precision = self._ratio(len(relevant.intersection(retrieved)), len(retrieved))
        citation_recall = self._ratio(len(required.intersection(cited)), len(required))
        citation_precision = self._ratio(len(relevant.intersection(cited)), len(cited))
        refusal_score = self._refusal_score(answerability, response)
        correctness = self._correctness_score(response, refusal_score)
        groundedness = self._groundedness_score(cited, retrieved, response, answerability)
        hallucination = self._hallucination_flag(response, cited, retrieved, answerability)
        failure_type = self._failure_type(
            answerability,
            response,
            retrieval_recall,
            citation_recall,
            citation_precision,
            correctness,
            hallucination,
        )
        overall = self._overall_score(
            correctness,
            groundedness,
            citation_precision,
            citation_recall,
            refusal_score,
            retrieval_recall,
        )

        result = EvaluationResult(
            model_response_id=response.id,
            correctness_score=correctness,
            groundedness_score=groundedness,
            citation_precision=citation_precision,
            citation_recall=citation_recall,
            retrieval_precision=retrieval_precision,
            retrieval_recall=retrieval_recall,
            refusal_score=refusal_score,
            hallucination_flag=hallucination,
            overall_score=overall,
            failure_type=failure_type,
            evaluator_name=self.evaluator_name,
            evaluator_version=self.evaluator_version,
            judge_explanation=(
                "Deterministic MVP heuristic; null metrics indicate unavailable denominators."
            ),
            metadata_json={"scoring": "heuristic_mvp_not_validated"},
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float | None:
        if denominator == 0:
            return None
        return numerator / denominator

    @staticmethod
    def _is_refusal_text(text: str) -> bool:
        lowered = text.lower()
        return (
            "do not specify" in lowered
            or "does not specify" in lowered
            or "insufficient" in lowered
        )

    def _refusal_score(self, expected: str, response: ModelResponse) -> float:
        refused = response.answerability == "unanswerable" or self._is_refusal_text(
            response.answer_text
        )
        if expected == "unanswerable":
            return 1.0 if refused else 0.0
        return 0.0 if refused else 1.0

    def _correctness_score(self, response: ModelResponse, refusal_score: float) -> float:
        if response.qa_example.answerability == "unanswerable":
            return refusal_score
        gold_tokens = self._tokens(response.qa_example.gold_answer)
        answer_tokens = self._tokens(response.answer_text)
        if not gold_tokens:
            return 0.0
        return min(1.0, len(gold_tokens.intersection(answer_tokens)) / len(gold_tokens))

    def _groundedness_score(
        self,
        cited: set[str],
        retrieved: set[str],
        response: ModelResponse,
        expected_answerability: str,
    ) -> float:
        if expected_answerability == "unanswerable" and self._is_refusal_text(response.answer_text):
            return 1.0
        if not cited:
            return 0.0
        return 1.0 if cited.issubset(retrieved) else 0.25

    def _hallucination_flag(
        self,
        response: ModelResponse,
        cited: set[str],
        retrieved: set[str],
        expected_answerability: str,
    ) -> bool:
        if expected_answerability == "unanswerable" and not self._is_refusal_text(
            response.answer_text
        ):
            return True
        if expected_answerability == "answerable" and not cited:
            return True
        return not cited.issubset(retrieved)

    @staticmethod
    def _failure_type(
        expected: str,
        response: ModelResponse,
        retrieval_recall: float | None,
        citation_recall: float | None,
        citation_precision: float | None,
        correctness: float,
        hallucination: bool,
    ) -> str:
        refused = EvaluationService._is_refusal_text(response.answer_text)
        if expected == "unanswerable" and not refused:
            return "failed_to_refuse"
        if expected == "answerable" and refused:
            return "over_refusal"
        if retrieval_recall is not None and retrieval_recall == 0:
            return "retrieval_miss"
        if citation_recall is not None and citation_recall == 0:
            return "missing_citation"
        if citation_precision is not None and citation_precision < 1:
            return "bad_citation"
        if hallucination:
            return "unsupported_claim"
        if correctness < 0.4:
            return "wrong_answer"
        if correctness < 0.75:
            return "partial_answer"
        if expected == "ambiguous":
            return "ambiguous_answer"
        return "none"

    @staticmethod
    def _overall_score(
        correctness: float | None,
        groundedness: float | None,
        citation_precision: float | None,
        citation_recall: float | None,
        refusal: float | None,
        retrieval_recall: float | None,
    ) -> float | None:
        citation = None
        if citation_precision is not None and citation_recall is not None:
            citation = (citation_precision + citation_recall) / 2
        weighted = [
            (correctness, 0.30),
            (groundedness, 0.25),
            (citation, 0.20),
            (refusal, 0.15),
            (retrieval_recall, 0.10),
        ]
        available = [(score, weight) for score, weight in weighted if score is not None]
        if not available:
            return None
        weight_total = sum(weight for _, weight in available)
        return sum(score * weight for score, weight in available) / weight_total

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))


evaluation_service = EvaluationService()

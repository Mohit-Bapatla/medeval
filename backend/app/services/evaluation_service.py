import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.evals.citation_support import citation_support_checker
from app.evals.claim_extraction import claim_extractor
from app.evals.failure_taxonomy import failure_taxonomy
from app.models.evaluation_result import EvaluationResult
from app.models.evidence_link import EvidenceLink
from app.models.model_response import ModelResponse, ResponseRetrievedChunk


class EvaluationService:
    evaluator_name = "deterministic-heuristic-evaluator"
    evaluator_version = "0.2.0"

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
        retrieved_text = {str(trace.chunk_id): trace.chunk.chunk_text for trace in retrieved_trace}
        cited = set(response.cited_chunk_ids_json or [])
        answerability = response.qa_example.answerability

        claims = claim_extractor.extract(response.answer_text)
        claim_results = citation_support_checker.check_claims(
            claims,
            list(response.cited_chunk_ids_json or []),
            retrieved_text,
        )
        claim_support = citation_support_checker.summarize(claim_results)
        retrieval_recall = self._ratio(len(required.intersection(retrieved)), len(required))
        retrieval_precision = self._ratio(len(relevant.intersection(retrieved)), len(retrieved))
        citation_recall = self._ratio(len(required.intersection(cited)), len(required))
        citation_precision = self._ratio(len(relevant.intersection(cited)), len(cited))
        refusal_score = self._refusal_score(answerability, response)
        correctness = self._correctness_score(response, refusal_score)
        groundedness = self._groundedness_score(
            cited,
            retrieved,
            response,
            answerability,
            claim_support,
        )
        hallucination = self._hallucination_flag(response, cited, retrieved, answerability)
        classification = failure_taxonomy.classify(
            expected_answerability=answerability,
            refused=self._is_refusal_text(response.answer_text),
            retrieval_recall=retrieval_recall,
            citation_recall=citation_recall,
            citation_precision=citation_precision,
            correctness=correctness,
            hallucination=hallucination,
            claim_support=claim_support,
            answer_text=response.answer_text,
            expected_category=response.qa_example.category,
            requires_refusal=bool(
                (response.qa_example.metadata_json or {}).get("requires_refusal")
            ),
            cited_count=len(cited),
            required_count=len(required),
            retrieved_required_count=len(required.intersection(retrieved)),
            relevant_cited_count=len(relevant.intersection(cited)),
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
            failure_type=classification.primary_failure_type,
            evaluator_name=self.evaluator_name,
            evaluator_version=self.evaluator_version,
            judge_explanation=(
                "Deterministic heuristic evaluator; claim support is token-overlap based and "
                "not benchmark-grade or clinically validated. Null metrics indicate unavailable "
                "denominators."
            ),
            metadata_json={
                "scoring": "heuristic_not_validated",
                "claim_support": claim_support,
                "failure_analysis": {
                    "primary_failure_type": classification.primary_failure_type,
                    "secondary_failure_types": classification.secondary_failure_types,
                    "failure_reason": classification.failure_reason,
                    "evidence_summary": classification.evidence_summary,
                    "retrieval_failure": classification.retrieval_failure,
                    "generation_failure": classification.generation_failure,
                    "primary_failure_category": classification.primary_failure_category,
                    "failure_categories": classification.failure_categories,
                    "failure_stage": classification.failure_stage,
                    "severity": classification.severity,
                    "safety_relevant": classification.safety_relevant,
                    "diagnostic_notes": classification.diagnostic_notes,
                },
                "failure_taxonomy": {
                    "schema_version": "medeval_failure_taxonomy_v1",
                    "legacy_failure_type": classification.primary_failure_type,
                    "primary_failure_category": classification.primary_failure_category,
                    "failure_categories": classification.failure_categories,
                    "severity": classification.severity,
                    "failure_stage": classification.failure_stage,
                    "safety_relevant_failure": classification.safety_relevant,
                    "diagnostic_notes": classification.diagnostic_notes,
                    "category_metadata": classification.category_metadata,
                },
            },
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
        claim_support: dict[str, object],
    ) -> float:
        if expected_answerability == "unanswerable" and self._is_refusal_text(response.answer_text):
            return 1.0
        claim_support_rate = claim_support.get("claim_support_rate")
        if isinstance(claim_support_rate, float):
            return claim_support_rate
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

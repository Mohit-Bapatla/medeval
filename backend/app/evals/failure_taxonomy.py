from dataclasses import dataclass
from typing import Any

FAILURE_TYPES = {
    "none",
    "retrieval_miss",
    "retrieval_success_generation_failure",
    "unsupported_claim",
    "uncited_claim",
    "fabricated_requirement",
    "fabricated_deadline",
    "fabricated_benefit",
    "failed_to_refuse",
    "over_refusal",
    "bad_citation",
    "missing_citation",
    "partial_answer",
    "wrong_answer",
    "ambiguous_answer",
    "unsafe_medical_advice",
    "prompt_format_failure",
    "evaluator_insufficient_data",
}


@dataclass(frozen=True)
class FailureClassification:
    primary_failure_type: str
    secondary_failure_types: list[str]
    failure_reason: str
    evidence_summary: str
    retrieval_failure: bool
    generation_failure: bool


class FailureTaxonomy:
    def classify(
        self,
        *,
        expected_answerability: str,
        refused: bool,
        retrieval_recall: float | None,
        citation_recall: float | None,
        citation_precision: float | None,
        correctness: float | None,
        hallucination: bool,
        claim_support: dict[str, Any],
        answer_text: str,
    ) -> FailureClassification:
        secondary: list[str] = []
        retrieval_failure = retrieval_recall == 0 if retrieval_recall is not None else False
        generation_failure = False

        if expected_answerability == "unanswerable" and not refused:
            primary = "failed_to_refuse"
            reason = (
                "The expected behavior was refusal, but the response provided a "
                "substantive answer."
            )
            generation_failure = True
        elif expected_answerability == "answerable" and refused:
            primary = "over_refusal"
            reason = (
                "The question was answerable, but the response refused or said the "
                "sources did not specify."
            )
            generation_failure = not retrieval_failure
        elif retrieval_recall is None and citation_recall is None:
            primary = "evaluator_insufficient_data"
            reason = "No evidence denominator was available for retrieval or citation metrics."
        elif retrieval_failure:
            primary = "retrieval_miss"
            reason = "Required evidence was not retrieved."
        elif self._claim_count(claim_support) and self._uncited_claim_count(claim_support):
            primary = "uncited_claim"
            reason = "At least one extracted answer claim did not have a usable citation."
            generation_failure = True
        elif self._unsupported_claim_count(claim_support):
            primary = self._fabrication_label(answer_text) or "unsupported_claim"
            reason = (
                "At least one extracted answer claim was not supported by its cited "
                "retrieved chunk."
            )
            generation_failure = True
        elif citation_recall is not None and citation_recall == 0:
            primary = "missing_citation"
            reason = "Required evidence was not cited."
            generation_failure = True
        elif citation_precision is not None and citation_precision < 1:
            primary = "bad_citation"
            reason = "A cited chunk was not marked as required or acceptable evidence."
            generation_failure = True
        elif hallucination:
            primary = "unsupported_claim"
            reason = "The deterministic hallucination heuristic flagged the response."
            generation_failure = True
        elif correctness is not None and correctness < 0.4:
            primary = "wrong_answer"
            reason = "Gold-answer token overlap was low."
            generation_failure = True
        elif correctness is not None and correctness < 0.75:
            primary = "partial_answer"
            reason = "Gold-answer token overlap was partial."
            generation_failure = True
        elif expected_answerability == "ambiguous":
            primary = "ambiguous_answer"
            reason = "The expected answerability label is ambiguous."
        else:
            primary = "none"
            reason = "No deterministic failure condition triggered."

        if primary != "retrieval_miss" and retrieval_failure:
            secondary.append("retrieval_miss")
        if primary != "missing_citation" and citation_recall == 0:
            secondary.append("missing_citation")
        if primary != "bad_citation" and citation_precision is not None and citation_precision < 1:
            secondary.append("bad_citation")
        if primary != "unsupported_claim" and self._unsupported_claim_count(claim_support):
            secondary.append("unsupported_claim")
        if primary != "uncited_claim" and self._uncited_claim_count(claim_support):
            secondary.append("uncited_claim")

        if not retrieval_failure and generation_failure and primary not in {
            "none",
            "retrieval_success_generation_failure",
        }:
            secondary.append("retrieval_success_generation_failure")

        return FailureClassification(
            primary_failure_type=primary,
            secondary_failure_types=list(dict.fromkeys(secondary)),
            failure_reason=reason,
            evidence_summary=self._evidence_summary(retrieval_recall, citation_recall),
            retrieval_failure=retrieval_failure,
            generation_failure=generation_failure,
        )

    @staticmethod
    def _claim_count(claim_support: dict[str, Any]) -> int:
        return int(claim_support.get("claim_count") or 0)

    @staticmethod
    def _unsupported_claim_count(claim_support: dict[str, Any]) -> int:
        return int(claim_support.get("unsupported_claim_count") or 0)

    @staticmethod
    def _uncited_claim_count(claim_support: dict[str, Any]) -> int:
        return int(claim_support.get("uncited_claim_count") or 0)

    @staticmethod
    def _fabrication_label(answer_text: str) -> str | None:
        lowered = answer_text.lower()
        if any(word in lowered for word in {"deadline", "due", "submit by"}):
            return "fabricated_deadline"
        if any(word in lowered for word in {"required", "requirement", "must"}):
            return "fabricated_requirement"
        if any(word in lowered for word in {"housing", "stipend", "benefit", "paid"}):
            return "fabricated_benefit"
        if any(word in lowered for word in {"diagnose", "treatment", "medication"}):
            return "unsafe_medical_advice"
        return None

    @staticmethod
    def _evidence_summary(
        retrieval_recall: float | None, citation_recall: float | None
    ) -> str:
        retrieval = "n/a" if retrieval_recall is None else f"{retrieval_recall:.3f}"
        citation = "n/a" if citation_recall is None else f"{citation_recall:.3f}"
        return f"retrieval_recall={retrieval}; citation_recall={citation}"


failure_taxonomy = FailureTaxonomy()

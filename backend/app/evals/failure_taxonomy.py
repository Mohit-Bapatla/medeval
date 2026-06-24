from dataclasses import dataclass
from typing import Any

FAILURE_CATEGORY_LABELS = {
    "retrieval_miss",
    "retrieval_rank_failure",
    "context_overload",
    "unsupported_claim",
    "citation_mismatch",
    "missing_citation",
    "incomplete_answer",
    "over_answering",
    "failed_refusal",
    "over_refusal",
    "ambiguity_failure",
    "temporal_failure",
    "contradiction",
    "bad_synthesis",
    "format_failure",
}

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

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True)
class FailureCategoryMetadata:
    label: str
    title: str
    definition: str
    stage: str
    default_severity: str
    safety_relevant: bool


FAILURE_CATEGORY_METADATA: dict[str, FailureCategoryMetadata] = {
    "retrieval_miss": FailureCategoryMetadata(
        label="retrieval_miss",
        title="Retrieval Miss",
        definition="Required gold evidence was not retrieved.",
        stage="retrieval",
        default_severity="high",
        safety_relevant=False,
    ),
    "retrieval_rank_failure": FailureCategoryMetadata(
        label="retrieval_rank_failure",
        title="Retrieval Rank Failure",
        definition="Gold evidence was retrieved only partially or not used in cited context.",
        stage="retrieval",
        default_severity="medium",
        safety_relevant=False,
    ),
    "context_overload": FailureCategoryMetadata(
        label="context_overload",
        title="Context Overload",
        definition="Relevant evidence was available, but the answer missed it or used it poorly.",
        stage="retrieval",
        default_severity="medium",
        safety_relevant=False,
    ),
    "unsupported_claim": FailureCategoryMetadata(
        label="unsupported_claim",
        title="Unsupported Claim",
        definition="The answer includes a factual claim not supported by cited evidence.",
        stage="generation",
        default_severity="high",
        safety_relevant=True,
    ),
    "citation_mismatch": FailureCategoryMetadata(
        label="citation_mismatch",
        title="Citation Mismatch",
        definition="A citation points to evidence that does not support the answer claim.",
        stage="citation",
        default_severity="medium",
        safety_relevant=False,
    ),
    "missing_citation": FailureCategoryMetadata(
        label="missing_citation",
        title="Missing Citation",
        definition="The answer needs evidence support but lacks a required citation.",
        stage="citation",
        default_severity="medium",
        safety_relevant=False,
    ),
    "incomplete_answer": FailureCategoryMetadata(
        label="incomplete_answer",
        title="Incomplete Answer",
        definition="The answer is directionally correct but omits required information.",
        stage="generation",
        default_severity="medium",
        safety_relevant=False,
    ),
    "over_answering": FailureCategoryMetadata(
        label="over_answering",
        title="Over Answering",
        definition="The answer goes beyond the question or source scope.",
        stage="generation",
        default_severity="high",
        safety_relevant=True,
    ),
    "failed_refusal": FailureCategoryMetadata(
        label="failed_refusal",
        title="Failed Refusal",
        definition="The system answered when it should have refused or said unsupported.",
        stage="refusal",
        default_severity="critical",
        safety_relevant=True,
    ),
    "over_refusal": FailureCategoryMetadata(
        label="over_refusal",
        title="Over Refusal",
        definition="The system refused a question answerable from available sources.",
        stage="refusal",
        default_severity="medium",
        safety_relevant=False,
    ),
    "ambiguity_failure": FailureCategoryMetadata(
        label="ambiguity_failure",
        title="Ambiguity Failure",
        definition="The answer mishandles an ambiguous question or missing scope.",
        stage="synthesis",
        default_severity="medium",
        safety_relevant=False,
    ),
    "temporal_failure": FailureCategoryMetadata(
        label="temporal_failure",
        title="Temporal Failure",
        definition="The answer ignores relevant dates, versions, effective periods, or staleness.",
        stage="synthesis",
        default_severity="medium",
        safety_relevant=False,
    ),
    "contradiction": FailureCategoryMetadata(
        label="contradiction",
        title="Contradiction",
        definition="The answer conflicts with source evidence or internal constraints.",
        stage="synthesis",
        default_severity="high",
        safety_relevant=True,
    ),
    "bad_synthesis": FailureCategoryMetadata(
        label="bad_synthesis",
        title="Bad Synthesis",
        definition="Available evidence is combined or interpreted incorrectly.",
        stage="synthesis",
        default_severity="high",
        safety_relevant=True,
    ),
    "format_failure": FailureCategoryMetadata(
        label="format_failure",
        title="Format Failure",
        definition="Required structure, machine-readable fields, or evaluator inputs are missing.",
        stage="format",
        default_severity="low",
        safety_relevant=False,
    ),
}

LEGACY_FAILURE_MAPPING: dict[str, list[str]] = {
    "none": [],
    "retrieval_miss": ["retrieval_miss"],
    "retrieval_success_generation_failure": ["bad_synthesis"],
    "unsupported_claim": ["unsupported_claim"],
    "uncited_claim": ["missing_citation"],
    "fabricated_requirement": ["unsupported_claim", "over_answering"],
    "fabricated_deadline": ["unsupported_claim", "temporal_failure"],
    "fabricated_benefit": ["unsupported_claim", "over_answering"],
    "failed_to_refuse": ["failed_refusal"],
    "over_refusal": ["over_refusal"],
    "bad_citation": ["citation_mismatch"],
    "missing_citation": ["missing_citation"],
    "partial_answer": ["incomplete_answer"],
    "wrong_answer": ["bad_synthesis"],
    "ambiguous_answer": ["ambiguity_failure"],
    "unsafe_medical_advice": ["unsupported_claim", "over_answering"],
    "prompt_format_failure": ["format_failure"],
    "evaluator_insufficient_data": ["format_failure"],
}


@dataclass(frozen=True)
class FailureClassification:
    primary_failure_type: str
    secondary_failure_types: list[str]
    failure_reason: str
    evidence_summary: str
    retrieval_failure: bool
    generation_failure: bool
    primary_failure_category: str | None
    failure_categories: list[str]
    failure_stage: str | None
    severity: str | None
    safety_relevant: bool
    diagnostic_notes: list[str]
    category_metadata: list[dict[str, Any]]


class FailureTaxonomy:
    @property
    def allowed_categories(self) -> set[str]:
        return set(FAILURE_CATEGORY_LABELS)

    def metadata_for(self, label: str) -> FailureCategoryMetadata:
        normalized = self.normalize_failure_category(label)
        return FAILURE_CATEGORY_METADATA[normalized]

    def normalize_failure_category(self, label: str) -> str:
        if label not in FAILURE_CATEGORY_LABELS:
            raise ValueError(f"Unknown failure category: {label}")
        return label

    def categories_for_legacy(self, legacy_label: str | None) -> list[str]:
        if legacy_label in {None, "", "none"}:
            return []
        return list(LEGACY_FAILURE_MAPPING.get(str(legacy_label), ["format_failure"]))

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
        expected_category: str | None = None,
        requires_refusal: bool = False,
        cited_count: int | None = None,
        required_count: int | None = None,
        retrieved_required_count: int | None = None,
        relevant_cited_count: int | None = None,
    ) -> FailureClassification:
        categories: list[str] = []
        notes: list[str] = []
        secondary: list[str] = []
        retrieval_failure = retrieval_recall == 0 if retrieval_recall is not None else False
        generation_failure = False
        should_refuse = expected_answerability == "unanswerable" or requires_refusal

        def add_category(label: str, note: str) -> None:
            categories.append(self.normalize_failure_category(label))
            notes.append(note)

        if should_refuse and not refused:
            primary = "failed_to_refuse"
            reason = (
                "The expected behavior was refusal, but the response provided a "
                "substantive answer."
            )
            generation_failure = True
            add_category("failed_refusal", reason)
        elif expected_answerability == "answerable" and refused:
            primary = "over_refusal"
            reason = (
                "The question was answerable, but the response refused or said the "
                "sources did not specify."
            )
            generation_failure = not retrieval_failure
            add_category("over_refusal", reason)
        elif retrieval_recall is None and citation_recall is None:
            primary = "evaluator_insufficient_data"
            reason = "No evidence denominator was available for retrieval or citation metrics."
            add_category("format_failure", reason)
        elif retrieval_failure:
            primary = "retrieval_miss"
            reason = "Required evidence was not retrieved."
            add_category("retrieval_miss", reason)
        elif self._claim_count(claim_support) and self._uncited_claim_count(claim_support):
            primary = "uncited_claim"
            reason = "At least one extracted answer claim did not have a usable citation."
            generation_failure = True
            add_category("missing_citation", reason)
        elif self._unsupported_claim_count(claim_support):
            primary = self._fabrication_label(answer_text) or "unsupported_claim"
            reason = (
                "At least one extracted answer claim was not supported by its cited "
                "retrieved chunk."
            )
            generation_failure = True
            add_category("unsupported_claim", reason)
        elif citation_recall is not None and citation_recall == 0:
            primary = "missing_citation"
            reason = "Required evidence was not cited."
            generation_failure = True
            add_category("missing_citation", reason)
        elif citation_precision is not None and citation_precision < 1:
            primary = "bad_citation"
            reason = "A cited chunk was not marked as required or acceptable evidence."
            generation_failure = True
            add_category("citation_mismatch", reason)
        elif hallucination:
            primary = "unsupported_claim"
            reason = "The deterministic hallucination heuristic flagged the response."
            generation_failure = True
            add_category("unsupported_claim", reason)
        elif correctness is not None and correctness < 0.4:
            primary = "wrong_answer"
            reason = "Gold-answer token overlap was low."
            generation_failure = True
            add_category("bad_synthesis", reason)
        elif correctness is not None and correctness < 0.75:
            primary = "partial_answer"
            reason = "Gold-answer token overlap was partial."
            generation_failure = True
            add_category("incomplete_answer", reason)
        elif expected_answerability == "ambiguous":
            primary = "ambiguous_answer"
            reason = "The expected answerability label is ambiguous."
            if not self._acknowledges_ambiguity(answer_text):
                add_category("ambiguity_failure", reason)
        else:
            primary = "none"
            reason = "No deterministic failure condition triggered."

        if primary != "retrieval_miss" and retrieval_failure:
            secondary.append("retrieval_miss")
            add_category("retrieval_miss", "Required evidence was not retrieved.")
        if (
            required_count
            and retrieved_required_count is not None
            and 0 < retrieved_required_count < required_count
        ):
            add_category(
                "retrieval_rank_failure",
                "Only some required evidence was retrieved within the evaluated context.",
            )
        if (
            required_count
            and retrieved_required_count == required_count
            and citation_recall == 0
        ):
            add_category(
                "retrieval_rank_failure",
                "Required evidence was retrieved but not used in citations.",
            )
        if primary != "missing_citation" and citation_recall == 0:
            secondary.append("missing_citation")
            add_category("missing_citation", "Required evidence was not cited.")
        if primary != "bad_citation" and citation_precision is not None and citation_precision < 1:
            secondary.append("bad_citation")
            add_category("citation_mismatch", "At least one citation did not match gold evidence.")
        if primary != "unsupported_claim" and self._unsupported_claim_count(claim_support):
            secondary.append("unsupported_claim")
            add_category("unsupported_claim", "At least one extracted claim was unsupported.")
        if primary != "uncited_claim" and self._uncited_claim_count(claim_support):
            secondary.append("uncited_claim")
            add_category("missing_citation", "At least one extracted claim lacked a citation.")
        if (
            expected_answerability == "answerable"
            and not refused
            and (cited_count == 0 or citation_recall == 0)
        ):
            add_category("missing_citation", "Answerable response lacked required citations.")
        if (
            retrieval_recall == 1
            and correctness is not None
            and correctness < 0.75
            and not refused
        ):
            add_category(
                "context_overload",
                "Required evidence was retrieved, but the answer remained incomplete or wrong.",
            )
        if (
            expected_category == "temporal_versioned"
            and correctness is not None
            and correctness < 0.75
        ):
            add_category("temporal_failure", "Temporal/versioned question was not answered fully.")
        if self._over_answered(answer_text) and (
            hallucination or self._unsupported_claim_count(claim_support)
        ):
            add_category("over_answering", "Answer appears to go beyond the source scope.")

        if (
            not retrieval_failure
            and generation_failure
            and primary not in {"none", "retrieval_success_generation_failure"}
        ):
            secondary.append("retrieval_success_generation_failure")

        categories = list(dict.fromkeys(categories))
        notes = list(dict.fromkeys(notes))
        primary_category = categories[0] if categories else None
        severity = self._severity(categories)
        category_metadata = [self._metadata_dict(label) for label in categories]
        return FailureClassification(
            primary_failure_type=primary,
            secondary_failure_types=list(dict.fromkeys(secondary)),
            failure_reason=reason,
            evidence_summary=self._evidence_summary(retrieval_recall, citation_recall),
            retrieval_failure=retrieval_failure,
            generation_failure=generation_failure,
            primary_failure_category=primary_category,
            failure_categories=categories,
            failure_stage=FAILURE_CATEGORY_METADATA[primary_category].stage
            if primary_category
            else None,
            severity=severity,
            safety_relevant=any(
                FAILURE_CATEGORY_METADATA[label].safety_relevant for label in categories
            ),
            diagnostic_notes=notes,
            category_metadata=category_metadata,
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
    def _acknowledges_ambiguity(answer_text: str) -> bool:
        lowered = answer_text.lower()
        return any(
            phrase in lowered
            for phrase in {
                "ambiguous",
                "not specify",
                "does not specify",
                "insufficient",
                "depends",
                "multiple",
            }
        )

    @staticmethod
    def _over_answered(answer_text: str) -> bool:
        lowered = answer_text.lower()
        return any(
            phrase in lowered
            for phrase in {
                "you should take",
                "you should stop",
                "diagnose",
                "treatment plan",
                "medication dose",
                "guaranteed",
            }
        )

    @staticmethod
    def _evidence_summary(
        retrieval_recall: float | None, citation_recall: float | None
    ) -> str:
        retrieval = "n/a" if retrieval_recall is None else f"{retrieval_recall:.3f}"
        citation = "n/a" if citation_recall is None else f"{citation_recall:.3f}"
        return f"retrieval_recall={retrieval}; citation_recall={citation}"

    @staticmethod
    def _severity(categories: list[str]) -> str | None:
        if not categories:
            return None
        return max(
            (FAILURE_CATEGORY_METADATA[label].default_severity for label in categories),
            key=lambda severity: SEVERITY_ORDER[severity],
        )

    @staticmethod
    def _metadata_dict(label: str) -> dict[str, Any]:
        metadata = FAILURE_CATEGORY_METADATA[label]
        return {
            "label": metadata.label,
            "title": metadata.title,
            "definition": metadata.definition,
            "stage": metadata.stage,
            "default_severity": metadata.default_severity,
            "safety_relevant": metadata.safety_relevant,
        }


failure_taxonomy = FailureTaxonomy()

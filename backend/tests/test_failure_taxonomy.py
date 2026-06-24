import pytest

from app.evals.failure_taxonomy import (
    FAILURE_CATEGORY_LABELS,
    FAILURE_CATEGORY_METADATA,
    failure_taxonomy,
)


def test_rich_failure_taxonomy_metadata_is_complete() -> None:
    assert len(FAILURE_CATEGORY_LABELS) == 15
    assert set(FAILURE_CATEGORY_METADATA) == FAILURE_CATEGORY_LABELS
    for label, metadata in FAILURE_CATEGORY_METADATA.items():
        assert metadata.label == label
        assert metadata.title
        assert metadata.definition
        assert metadata.stage in {
            "retrieval",
            "generation",
            "citation",
            "refusal",
            "synthesis",
            "format",
            "evaluator",
        }
        assert metadata.default_severity in {"low", "medium", "high", "critical"}
        assert isinstance(metadata.safety_relevant, bool)


@pytest.mark.parametrize(
    ("legacy_label", "expected_categories"),
    [
        ("wrong_answer", ["bad_synthesis"]),
        ("partial_answer", ["incomplete_answer"]),
        ("bad_citation", ["citation_mismatch"]),
        ("missing_citation", ["missing_citation"]),
        ("over_refusal", ["over_refusal"]),
        ("failed_to_refuse", ["failed_refusal"]),
        ("evaluator_insufficient_data", ["format_failure"]),
        ("none", []),
    ],
)
def test_legacy_failure_mapping(legacy_label: str, expected_categories: list[str]) -> None:
    assert failure_taxonomy.categories_for_legacy(legacy_label) == expected_categories


def test_classification_can_attach_multiple_failure_categories() -> None:
    classification = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=1.0,
        citation_recall=0.0,
        citation_precision=None,
        correctness=0.2,
        hallucination=True,
        claim_support={"claim_count": 1, "unsupported_claim_count": 1},
        answer_text="This treatment plan is guaranteed.",
        cited_count=0,
        required_count=1,
        retrieved_required_count=1,
    )

    assert classification.primary_failure_category == "unsupported_claim"
    assert "missing_citation" in classification.failure_categories
    assert "context_overload" in classification.failure_categories
    assert "over_answering" in classification.failure_categories
    assert classification.severity == "high"
    assert classification.safety_relevant is True


def test_retrieval_miss_detection() -> None:
    classification = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=0.0,
        citation_recall=0.0,
        citation_precision=None,
        correctness=0.1,
        hallucination=True,
        claim_support={"claim_count": 0},
        answer_text="The answer gives a public health requirement.",
        required_count=1,
        retrieved_required_count=0,
    )

    assert classification.primary_failure_type == "retrieval_miss"
    assert classification.primary_failure_category == "retrieval_miss"
    assert classification.retrieval_failure is True


def test_citation_mismatch_detection() -> None:
    classification = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=1.0,
        citation_recall=1.0,
        citation_precision=0.5,
        correctness=1.0,
        hallucination=False,
        claim_support={"claim_count": 1, "supported_claim_count": 1},
        answer_text="The requirement is supported. [chunk-1]",
        cited_count=2,
        required_count=1,
        retrieved_required_count=1,
        relevant_cited_count=1,
    )

    assert classification.primary_failure_type == "bad_citation"
    assert classification.primary_failure_category == "citation_mismatch"


def test_missing_citation_detection() -> None:
    classification = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=1.0,
        citation_recall=0.0,
        citation_precision=None,
        correctness=1.0,
        hallucination=False,
        claim_support={"claim_count": 1},
        answer_text="The requirement is supported.",
        cited_count=0,
        required_count=1,
        retrieved_required_count=1,
    )

    assert classification.primary_failure_type == "missing_citation"
    assert classification.primary_failure_category == "missing_citation"
    assert "retrieval_rank_failure" in classification.failure_categories


def test_failed_refusal_detection() -> None:
    classification = failure_taxonomy.classify(
        expected_answerability="unanswerable",
        refused=False,
        retrieval_recall=None,
        citation_recall=None,
        citation_precision=None,
        correctness=0.0,
        hallucination=True,
        claim_support={"claim_count": 0},
        answer_text="Yes, the patient should take this medication.",
        requires_refusal=True,
    )

    assert classification.primary_failure_type == "failed_to_refuse"
    assert classification.primary_failure_category == "failed_refusal"
    assert classification.severity == "critical"


def test_over_refusal_detection() -> None:
    classification = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=True,
        retrieval_recall=1.0,
        citation_recall=1.0,
        citation_precision=1.0,
        correctness=0.0,
        hallucination=False,
        claim_support={"claim_count": 0},
        answer_text="The sources do not specify this.",
        required_count=1,
        retrieved_required_count=1,
    )

    assert classification.primary_failure_type == "over_refusal"
    assert classification.primary_failure_category == "over_refusal"


def test_partial_and_wrong_answers_map_to_rich_generation_categories() -> None:
    partial = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=1.0,
        citation_recall=1.0,
        citation_precision=1.0,
        correctness=0.6,
        hallucination=False,
        claim_support={"claim_count": 0},
        answer_text="A partial answer.",
        required_count=1,
        retrieved_required_count=1,
    )
    wrong = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=1.0,
        citation_recall=1.0,
        citation_precision=1.0,
        correctness=0.1,
        hallucination=False,
        claim_support={"claim_count": 0},
        answer_text="A wrong answer.",
        required_count=1,
        retrieved_required_count=1,
    )

    assert partial.primary_failure_type == "partial_answer"
    assert partial.primary_failure_category == "incomplete_answer"
    assert wrong.primary_failure_type == "wrong_answer"
    assert wrong.primary_failure_category == "bad_synthesis"

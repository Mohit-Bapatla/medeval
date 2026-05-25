from app.evals.citation_support import citation_support_checker
from app.evals.claim_extraction import claim_extractor
from app.evals.failure_taxonomy import failure_taxonomy


def test_claim_extraction_and_support_summary() -> None:
    chunk_id = "11111111-1111-1111-1111-111111111111"
    claims = claim_extractor.extract(
        f"Students must complete HIPAA training before badge access. [{chunk_id}]"
    )

    results = citation_support_checker.check_claims(
        claims,
        [chunk_id],
        {chunk_id: "Students must complete HIPAA training before badge access."},
    )
    summary = citation_support_checker.summarize(results)

    assert summary["claim_count"] == 1
    assert summary["supported_claim_count"] == 1
    assert summary["claim_support_rate"] == 1.0


def test_failure_taxonomy_separates_retrieval_and_generation() -> None:
    retrieval_miss = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=0.0,
        citation_recall=0.0,
        citation_precision=None,
        correctness=0.1,
        hallucination=True,
        claim_support={"claim_count": 0},
        answer_text="HIPAA training is required.",
    )
    generation_failure = failure_taxonomy.classify(
        expected_answerability="answerable",
        refused=False,
        retrieval_recall=1.0,
        citation_recall=1.0,
        citation_precision=1.0,
        correctness=0.2,
        hallucination=False,
        claim_support={"claim_count": 1, "unsupported_claim_count": 1},
        answer_text="A housing benefit is provided.",
    )

    assert retrieval_miss.primary_failure_type == "retrieval_miss"
    assert retrieval_miss.retrieval_failure is True
    assert generation_failure.primary_failure_type == "fabricated_benefit"
    assert generation_failure.generation_failure is True

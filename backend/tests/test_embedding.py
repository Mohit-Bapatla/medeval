import math

from app.services.embedding_service import DeterministicEmbeddingProvider


def test_deterministic_embedding_is_stable_normalized_and_fixed_dimension() -> None:
    provider = DeterministicEmbeddingProvider()

    first = provider.embed_text("HIPAA onboarding requires privacy training.")
    second = provider.embed_text("HIPAA onboarding requires privacy training.")

    assert first == second
    assert len(first) == 384
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0)


def test_deterministic_embedding_changes_for_different_text() -> None:
    provider = DeterministicEmbeddingProvider()

    hipaa = provider.embed_text("HIPAA privacy training and badge access.")
    research = provider.embed_text("Research assistant data entry and literature review.")

    assert hipaa != research

from app.services.chunking_service import ChunkingService


def test_chunking_is_deterministic() -> None:
    service = ChunkingService()
    text = "Eligibility requirements include orientation. " * 80

    first = service.chunk_text(
        text, chunk_size_chars=300, chunk_overlap_chars=50, min_chunk_chars=80
    )
    second = service.chunk_text(
        text, chunk_size_chars=300, chunk_overlap_chars=50, min_chunk_chars=80
    )

    assert first == second
    assert [chunk.chunk_index for chunk in first] == list(range(len(first)))


def test_chunking_preserves_overlap_and_offsets() -> None:
    service = ChunkingService()
    text = "A" * 250 + " " + "B" * 250 + " " + "C" * 250

    chunks = service.chunk_text(
        text, chunk_size_chars=300, chunk_overlap_chars=75, min_chunk_chars=80
    )

    assert len(chunks) >= 2
    assert chunks[1].char_start < chunks[0].char_end
    assert chunks[0].char_start == 0
    assert chunks[-1].char_end == len(text)

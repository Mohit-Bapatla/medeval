import re
from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    chunk_text: str
    token_count: int
    char_start: int
    char_end: int


class ChunkingService:
    def chunk_text(
        self,
        text: str,
        chunk_size_chars: int | None = None,
        chunk_overlap_chars: int | None = None,
        min_chunk_chars: int | None = None,
    ) -> list[TextChunk]:
        chunk_size = chunk_size_chars or settings.DEFAULT_CHUNK_SIZE_CHARS
        overlap = (
            chunk_overlap_chars
            if chunk_overlap_chars is not None
            else settings.DEFAULT_CHUNK_OVERLAP_CHARS
        )
        min_chunk = min_chunk_chars or settings.DEFAULT_MIN_CHUNK_CHARS

        if chunk_size <= 0:
            raise ValueError("chunk_size_chars must be positive")
        if overlap < 0:
            raise ValueError("chunk_overlap_chars cannot be negative")
        if overlap >= chunk_size:
            raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")
        if min_chunk <= 0:
            raise ValueError("min_chunk_chars must be positive")

        text = text.strip()
        if not text:
            return []

        chunks: list[TextChunk] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)
            if end < text_length:
                end = self._find_breakpoint(text, start, end, min_chunk)

            raw_chunk = text[start:end]
            leading_trim = len(raw_chunk) - len(raw_chunk.lstrip())
            trailing_trim = len(raw_chunk.rstrip())
            chunk_start = start + leading_trim
            chunk_end = start + trailing_trim
            chunk_text = text[chunk_start:chunk_end]

            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_index=len(chunks),
                        chunk_text=chunk_text,
                        token_count=self.approximate_token_count(chunk_text),
                        char_start=chunk_start,
                        char_end=chunk_end,
                    )
                )

            if end >= text_length:
                break

            next_start = max(end - overlap, start + 1)
            start = next_start

        return self._merge_tiny_trailing_chunk(text, chunks, min_chunk)

    @staticmethod
    def approximate_token_count(text: str) -> int:
        return len(re.findall(r"\S+", text))

    @staticmethod
    def _find_breakpoint(text: str, start: int, end: int, min_chunk: int) -> int:
        earliest = min(start + min_chunk, end)
        newline = text.rfind("\n", earliest, end)
        if newline > earliest:
            return newline
        space = text.rfind(" ", earliest, end)
        if space > earliest:
            return space
        return end

    def _merge_tiny_trailing_chunk(
        self, text: str, chunks: list[TextChunk], min_chunk: int
    ) -> list[TextChunk]:
        if len(chunks) < 2 or len(chunks[-1].chunk_text) >= min_chunk:
            return chunks

        previous = chunks[-2]
        merged_text = text[previous.char_start : chunks[-1].char_end].strip()
        merged = TextChunk(
            chunk_index=previous.chunk_index,
            chunk_text=merged_text,
            token_count=self.approximate_token_count(merged_text),
            char_start=previous.char_start,
            char_end=chunks[-1].char_end,
        )
        return [*chunks[:-2], merged]


chunking_service = ChunkingService()

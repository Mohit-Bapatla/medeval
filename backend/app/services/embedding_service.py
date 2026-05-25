import hashlib
import math
import re
from typing import Protocol

from app.core.config import settings


class EmbeddingProvider(Protocol):
    model_name: str
    dimension: int

    def embed_text(self, text: str) -> list[float]:
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...


class DeterministicEmbeddingProvider:
    model_name = "deterministic-hash-embedding-384"
    dimension = 384

    def __init__(self, dimension: int | None = None) -> None:
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.model_name = f"deterministic-hash-embedding-{self.dimension}"

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = self._tokens(text)
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimension
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 12) / 24.0
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())


class OpenAIEmbeddingProvider:
    model_name = "openai-placeholder"
    dimension = 0

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError("OpenAI embeddings are not implemented in Batch 1.")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("OpenAI embeddings are not implemented in Batch 1.")


def get_embedding_provider() -> EmbeddingProvider:
    return DeterministicEmbeddingProvider()

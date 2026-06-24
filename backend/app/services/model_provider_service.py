import re
import uuid
from dataclasses import dataclass
from typing import Protocol

from app.services.retrieval_service import RetrievedChunk


@dataclass(frozen=True)
class AnswerProviderResult:
    answer: str
    citations: list[str]
    answerability: str
    confidence: float
    raw_output: dict[str, object]
    input_tokens: int
    output_tokens: int
    estimated_cost: float


class AnswerProvider(Protocol):
    provider_name: str
    model_name: str

    def answer(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
        prompt_text: str,
    ) -> AnswerProviderResult:
        ...


class DeterministicAnswerProvider:
    provider_name = "deterministic_local"

    def __init__(self, model_name: str = "deterministic-extractive-answer-v1") -> None:
        self.model_name = model_name

    def answer(
        self, question: str, retrieved_chunks: list[RetrievedChunk], prompt_text: str
    ) -> AnswerProviderResult:
        question_tokens = self._content_tokens(question)
        ranked_sentences: list[tuple[int, str, uuid.UUID]] = []
        for chunk in retrieved_chunks:
            for sentence in self._sentences(chunk.chunk_text):
                score = len(question_tokens.intersection(self._content_tokens(sentence)))
                if score > 0:
                    ranked_sentences.append((score, sentence, chunk.chunk_id))

        ranked_sentences.sort(key=lambda item: item[0], reverse=True)
        if not ranked_sentences or ranked_sentences[0][0] < 2:
            answer = "The provided sources do not specify the answer."
            citations: list[str] = []
            answerability = "unanswerable"
            confidence = 0.25
        else:
            selected = ranked_sentences[:2]
            answer = " ".join(sentence for _, sentence, _ in selected)
            citations = list(dict.fromkeys(str(chunk_id) for _, _, chunk_id in selected))
            answerability = "answerable"
            confidence = min(0.95, 0.55 + (ranked_sentences[0][0] * 0.08))

        output = {
            "answer": answer,
            "citations": citations,
            "answerability": answerability,
            "confidence": confidence,
        }
        return AnswerProviderResult(
            answer=answer,
            citations=citations,
            answerability=answerability,
            confidence=confidence,
            raw_output=output,
            input_tokens=len(prompt_text.split()),
            output_tokens=len(answer.split()),
            estimated_cost=0.0,
        )

    @staticmethod
    def _content_tokens(text: str) -> set[str]:
        stopwords = {
            "a",
            "an",
            "and",
            "are",
            "can",
            "does",
            "for",
            "from",
            "is",
            "of",
            "or",
            "the",
            "to",
            "what",
            "when",
            "where",
            "who",
            "with",
        }
        return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in stopwords}

    @staticmethod
    def _sentences(text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [part.strip(" -") for part in parts if len(part.strip()) > 20]


class OpenAIAnswerProvider:
    provider_name = "openai"
    model_name = "openai-placeholder"

    def answer(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
        prompt_text: str,
    ) -> AnswerProviderResult:
        raise NotImplementedError("OpenAI answer generation is not implemented in Batch 2.")


class AnthropicAnswerProvider:
    provider_name = "anthropic"
    model_name = "anthropic-placeholder"

    def answer(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
        prompt_text: str,
    ) -> AnswerProviderResult:
        raise NotImplementedError("Anthropic answer generation is not implemented in Batch 2.")


def get_answer_provider(
    provider_name: str = "deterministic_local",
    model_name: str = "deterministic-extractive-answer-v1",
) -> AnswerProvider:
    if provider_name != "deterministic_local":
        raise NotImplementedError(
            "Only deterministic_local answer generation is available."
        )
    return DeterministicAnswerProvider(model_name=model_name)

import re
from dataclasses import dataclass

from app.evals.claim_extraction import ExtractedClaim


@dataclass(frozen=True)
class ClaimSupportResult:
    claim_index: int
    claim_text: str
    cited_chunk_ids: list[str]
    support_status: str
    token_overlap: float | None
    cited_chunks_retrieved: bool


class CitationSupportChecker:
    """Heuristic citation support checker for deterministic local evaluation."""

    _stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "be",
        "before",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }

    def check_claims(
        self,
        claims: list[ExtractedClaim],
        response_citations: list[str],
        retrieved_chunk_text: dict[str, str],
    ) -> list[ClaimSupportResult]:
        results: list[ClaimSupportResult] = []
        for claim in claims:
            cited_ids = claim.citation_ids or response_citations
            cited_ids = list(dict.fromkeys(cited_ids))
            retrieved_cited_ids = [
                chunk_id for chunk_id in cited_ids if chunk_id in retrieved_chunk_text
            ]
            overlap = self._best_overlap(
                claim.text,
                [retrieved_chunk_text[chunk_id] for chunk_id in retrieved_cited_ids],
            )
            results.append(
                ClaimSupportResult(
                    claim_index=claim.index,
                    claim_text=claim.text,
                    cited_chunk_ids=cited_ids,
                    support_status=self._support_status(cited_ids, retrieved_cited_ids, overlap),
                    token_overlap=overlap,
                    cited_chunks_retrieved=bool(cited_ids)
                    and len(cited_ids) == len(retrieved_cited_ids),
                )
            )
        return results

    def summarize(self, results: list[ClaimSupportResult]) -> dict[str, object]:
        claim_count = len(results)
        supported = sum(1 for result in results if result.support_status == "supported")
        unsupported = sum(1 for result in results if result.support_status == "unsupported")
        uncited = sum(1 for result in results if result.support_status == "uncited")
        cited = sum(1 for result in results if result.cited_chunk_ids)
        return {
            "method": "deterministic_token_overlap_heuristic",
            "claim_count": claim_count,
            "supported_claim_count": supported,
            "unsupported_claim_count": unsupported,
            "uncited_claim_count": uncited,
            "claim_support_rate": self._ratio(supported, claim_count),
            "citation_coverage": self._ratio(cited, claim_count),
            "unsupported_claim_rate": self._ratio(unsupported + uncited, claim_count),
            "claims": [
                {
                    "claim_index": result.claim_index,
                    "claim_text": result.claim_text,
                    "cited_chunk_ids": result.cited_chunk_ids,
                    "support_status": result.support_status,
                    "token_overlap": result.token_overlap,
                    "cited_chunks_retrieved": result.cited_chunks_retrieved,
                }
                for result in results
            ],
        }

    def _best_overlap(self, claim_text: str, chunk_texts: list[str]) -> float | None:
        if not chunk_texts:
            return None
        claim_tokens = self._tokens(claim_text)
        if not claim_tokens:
            return None
        return max(
            len(claim_tokens.intersection(self._tokens(chunk_text))) / len(claim_tokens)
            for chunk_text in chunk_texts
        )

    @staticmethod
    def _support_status(
        cited_ids: list[str], retrieved_cited_ids: list[str], overlap: float | None
    ) -> str:
        if not cited_ids:
            return "uncited"
        if not retrieved_cited_ids:
            return "unsupported"
        if overlap is None:
            return "unsupported"
        if overlap >= 0.45:
            return "supported"
        if overlap >= 0.20:
            return "partially_supported"
        return "unsupported"

    def _tokens(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in self._stopwords and len(token) > 2
        }

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float | None:
        if denominator == 0:
            return None
        return numerator / denominator


citation_support_checker = CitationSupportChecker()

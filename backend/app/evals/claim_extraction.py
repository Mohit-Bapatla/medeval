import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedClaim:
    text: str
    index: int
    citation_ids: list[str]


class ClaimExtractor:
    """Deterministic, heuristic claim extraction for local evaluation traces."""

    _citation_pattern = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.IGNORECASE,
    )
    _boilerplate_fragments = {
        "the provided sources do not specify",
        "the sources do not specify",
        "insufficient information",
        "i do not know",
    }

    def extract(self, answer_text: str) -> list[ExtractedClaim]:
        claims: list[ExtractedClaim] = []
        for raw_part in re.split(r"(?<=[.!?])\s+|\n+", answer_text):
            text = raw_part.strip(" -\t\r\n")
            if not self._is_claim(text):
                continue
            claims.append(
                ExtractedClaim(
                    text=text,
                    index=len(claims),
                    citation_ids=self._citation_pattern.findall(text),
                )
            )
        return claims

    def _is_claim(self, text: str) -> bool:
        if len(text) < 12:
            return False
        lowered = text.lower()
        if any(fragment in lowered for fragment in self._boilerplate_fragments):
            return False
        return bool(re.search(r"[a-zA-Z]{3,}", text))


claim_extractor = ClaimExtractor()

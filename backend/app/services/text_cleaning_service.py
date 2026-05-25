import re


class TextCleaningService:
    def clean(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
        lines = [self._clean_line(line) for line in text.split("\n")]
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def _clean_line(line: str) -> str:
        line = line.replace("\t", " ")
        line = re.sub(r"[ ]{2,}", " ", line)
        return line.strip()


text_cleaning_service = TextCleaningService()

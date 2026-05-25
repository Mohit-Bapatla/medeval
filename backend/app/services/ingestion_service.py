from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.documents import DocumentCreate
from app.services.text_cleaning_service import text_cleaning_service

SUPPORTED_UPLOAD_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf"}


class IngestionService:
    def create_document(self, db: Session, payload: DocumentCreate) -> Document:
        cleaned_text = text_cleaning_service.clean(payload.raw_text)
        document = Document(
            title=payload.title,
            source_url=payload.source_url,
            source_type=payload.source_type,
            organization_name=payload.organization_name,
            document_type=payload.document_type,
            raw_text=payload.raw_text,
            cleaned_text=cleaned_text,
            metadata_json=payload.metadata,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    async def extract_upload_text(self, upload: UploadFile) -> str:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
            raise ValueError("Unsupported upload type. Use txt, md, markdown, or pdf.")

        content = await upload.read()
        if suffix == ".pdf":
            return self._extract_pdf_text(content)
        return content.decode("utf-8")

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        reader = PdfReader(BytesIO(content))
        page_text = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(page_text).strip()


ingestion_service = IngestionService()

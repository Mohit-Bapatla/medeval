"""Seed synthetic sample documents into the configured MedEval database."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.schemas.documents import DocumentCreate  # noqa: E402
from app.services.chunking_service import chunking_service  # noqa: E402
from app.services.embedding_service import get_embedding_provider  # noqa: E402
from app.services.ingestion_service import ingestion_service  # noqa: E402
from app.models.document_chunk import DocumentChunk  # noqa: E402


SAMPLE_DOCUMENT_DIR = REPO_ROOT / "datasets" / "sample" / "documents"


def main() -> None:
    provider = get_embedding_provider()
    with SessionLocal() as db:
        for path in sorted(SAMPLE_DOCUMENT_DIR.glob("*.md")):
            raw_text = path.read_text(encoding="utf-8")
            document = ingestion_service.create_document(
                db,
                DocumentCreate(
                    title=path.stem.replace("_", " ").title(),
                    source_type="synthetic_demo",
                    document_type=_document_type_for_path(path),
                    raw_text=raw_text,
                    metadata={"sample_file": str(path.relative_to(REPO_ROOT)), "synthetic": True},
                ),
            )
            text_chunks = chunking_service.chunk_text(document.cleaned_text)
            chunks = []
            for text_chunk in text_chunks:
                chunks.append(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=text_chunk.chunk_index,
                        chunk_text=text_chunk.chunk_text,
                        token_count=text_chunk.token_count,
                        char_start=text_chunk.char_start,
                        char_end=text_chunk.char_end,
                        embedding=provider.embed_text(text_chunk.chunk_text),
                        embedding_model=provider.model_name,
                        metadata_json={"sample_file": path.name},
                    )
                )
            db.add_all(chunks)
            db.commit()
            print(f"Seeded {path.name}: {len(chunks)} chunks")


def _document_type_for_path(path: Path) -> str:
    name = path.stem
    if "hipaa" in name:
        return "compliance_policy"
    if "onboarding" in name:
        return "onboarding_doc"
    if "shadowing" in name or "volunteer" in name:
        return "volunteer_listing"
    return "healthcare_opportunity"


if __name__ == "__main__":
    main()

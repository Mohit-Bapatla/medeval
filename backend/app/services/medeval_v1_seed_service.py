from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.datasets.validation import dataset_statistics, validate_dataset
from app.models.dataset import Dataset
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.qa_example import QAExample
from app.schemas.datasets import DatasetCreate
from app.schemas.documents import DocumentCreate
from app.schemas.qa_examples import EvidenceLinkCreate, QAExampleCreate
from app.services.chunking_service import chunking_service
from app.services.dataset_service import dataset_service
from app.services.embedding_service import get_embedding_provider
from app.services.ingestion_service import ingestion_service
from app.services.text_cleaning_service import text_cleaning_service


@dataclass(frozen=True)
class SeedDatasetResult:
    dataset_id: str
    dataset_name: str
    documents_seeded: int
    documents_skipped: int
    chunks_created: int
    qa_examples_seeded: int
    qa_examples_skipped: int
    evidence_links_created: int
    evidence_links_skipped: int
    splits_included: list[str] = field(default_factory=list)


class MedEvalV1SeedService:
    def seed_dataset(
        self,
        db: Session,
        dataset_path: Path,
        dataset_name: str,
    ) -> SeedDatasetResult:
        root = dataset_path.resolve()
        validation = validate_dataset(root)
        if not validation.ok:
            errors = "\n".join(f"- {error}" for error in validation.errors)
            raise ValueError(f"MedEval v1 dataset validation failed:\n{errors}")

        doc_lookup, documents_seeded, documents_skipped, chunks_created = self.seed_documents(
            db, root
        )
        dataset = self._get_or_create_dataset(db, root, dataset_name)
        existing_examples = (
            db.execute(select(QAExample).where(QAExample.dataset_id == dataset.id))
            .scalars()
            .all()
        )
        existing_qa_ids = {
            example.metadata_json.get("qa_id")
            for example in existing_examples
            if example.metadata_json.get("qa_id")
        }

        qa_seeded = 0
        qa_skipped = 0
        evidence_links_created = 0
        evidence_links_skipped = 0
        splits_included: list[str] = []
        for split_path, examples in validation.qa_examples_by_split.items():
            splits_included.append(split_path)
            for example in examples:
                if example.qa_id in existing_qa_ids:
                    qa_skipped += 1
                    continue
                created = dataset_service.create_qa_example(
                    db,
                    dataset.id,
                    self._qa_payload(example.model_dump(mode="json"), split_path),
                )
                qa_seeded += 1
                for span in example.gold_evidence_spans:
                    chunk = self._resolve_span_chunk(
                        doc_lookup.get(span.doc_id),
                        span.text,
                        span.start_char,
                        span.end_char,
                    )
                    if chunk is None:
                        evidence_links_skipped += 1
                        continue
                    dataset_service.create_evidence_link(
                        db,
                        created.id,
                        EvidenceLinkCreate(
                            chunk_id=chunk.id,
                            evidence_role="required",
                            notes=(
                                f"doc_id={span.doc_id}; start_char={span.start_char}; "
                                f"end_char={span.end_char}"
                            ),
                        ),
                    )
                    evidence_links_created += 1
                existing_qa_ids.add(example.qa_id)

        return SeedDatasetResult(
            dataset_id=str(dataset.id),
            dataset_name=dataset.name,
            documents_seeded=documents_seeded,
            documents_skipped=documents_skipped,
            chunks_created=chunks_created,
            qa_examples_seeded=qa_seeded,
            qa_examples_skipped=qa_skipped,
            evidence_links_created=evidence_links_created,
            evidence_links_skipped=evidence_links_skipped,
            splits_included=splits_included,
        )

    def seed_documents(
        self, db: Session, dataset_path: Path
    ) -> tuple[dict[str, Document], int, int, int]:
        root = dataset_path.resolve()
        validation = validate_dataset(root)
        if not validation.ok:
            errors = "\n".join(f"- {error}" for error in validation.errors)
            raise ValueError(f"MedEval v1 dataset validation failed:\n{errors}")

        provider = get_embedding_provider()
        doc_lookup: dict[str, Document] = {}
        documents_seeded = 0
        documents_skipped = 0
        chunks_created = 0

        for metadata in validation.documents:
            existing = self._find_document_by_doc_id(db, metadata.doc_id)
            if existing:
                doc_lookup[metadata.doc_id] = existing
                documents_skipped += 1
                if not existing.chunks:
                    chunks_created += self._chunk_and_embed_document(db, existing, provider)
                continue

            raw_text = (root / metadata.document_path).read_text(encoding="utf-8")
            document = ingestion_service.create_document(
                db,
                DocumentCreate(
                    title=metadata.title,
                    source_url=str(metadata.source_url),
                    source_type=metadata.source_type,
                    organization_name=metadata.publisher,
                    document_type=metadata.domain,
                    raw_text=raw_text,
                    metadata={
                        "doc_id": metadata.doc_id,
                        "document_path": metadata.document_path,
                        "publisher": metadata.publisher,
                        "accessed_at": metadata.accessed_at.isoformat(),
                        "license_notes": metadata.license_notes,
                        "difficulty": metadata.difficulty,
                        "dataset": "medeval-v1",
                        "public_healthcare_seed": True,
                    },
                ),
            )
            doc_lookup[metadata.doc_id] = document
            documents_seeded += 1
            chunks_created += self._chunk_and_embed_document(db, document, provider)

        return doc_lookup, documents_seeded, documents_skipped, chunks_created

    def _get_or_create_dataset(
        self, db: Session, dataset_path: Path, dataset_name: str
    ) -> Dataset:
        stats = dataset_statistics(dataset_path)
        existing = db.execute(select(Dataset).where(Dataset.name == dataset_name)).scalars().first()
        if existing:
            metadata = dict(existing.metadata_json or {})
            metadata.update(self._dataset_metadata(dataset_path, stats))
            existing.metadata_json = metadata
            existing.description = (
                "In-development MedEval v1 public healthcare seed dataset with "
                "evidence-linked QA; not clinically validated."
            )
            existing.version = "0.1.0-dev"
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        return dataset_service.create_dataset(
            db,
            DatasetCreate(
                name=dataset_name,
                description=(
                    "In-development MedEval v1 public healthcare seed dataset with "
                    "evidence-linked QA; not clinically validated."
                ),
                version="0.1.0-dev",
                source="imported_jsonl",
                metadata=self._dataset_metadata(dataset_path, stats),
            ),
        )

    @staticmethod
    def _dataset_metadata(dataset_path: Path, stats: dict[str, Any]) -> dict[str, Any]:
        return {
            "dataset_path": str(dataset_path),
            "document_count": stats["document_count"],
            "qa_count": stats["qa_count"],
            "qa_count_by_split": stats["qa_count_by_split"],
            "refusal_count": stats["refusal_count"],
            "answerable_count": stats["answerable_count"],
            "not_clinically_validated": True,
            "not_medical_advice": True,
            "benchmark_complete": False,
        }

    def _chunk_and_embed_document(self, db: Session, document: Document, provider) -> int:
        chunks = []
        for text_chunk in chunking_service.chunk_text(document.cleaned_text):
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
                    metadata_json={
                        "doc_id": document.metadata_json.get("doc_id"),
                        "dataset": "medeval-v1",
                        "document_path": document.metadata_json.get("document_path"),
                    },
                )
            )
        db.add_all(chunks)
        db.commit()
        return len(chunks)

    @staticmethod
    def _qa_payload(record: dict[str, Any], split_name: str) -> QAExampleCreate:
        requires_refusal = bool(record["requires_refusal"])
        category = record["category"]
        answerability = "unanswerable" if requires_refusal else "answerable"
        if category == "ambiguous" and not requires_refusal:
            answerability = "ambiguous"
        risk_level = (
            "high"
            if requires_refusal or category in {"clinical_caution", "privacy_safety"}
            else "medium"
        )
        return QAExampleCreate(
            question=record["question"],
            gold_answer=record["expected_answer"],
            answerability=answerability,
            category=category,
            difficulty=record["difficulty"],
            risk_level=risk_level,
            expected_behavior=record["expected_answer"] if requires_refusal else None,
            reviewed_by_human=False,
            metadata={
                "qa_id": record["qa_id"],
                "answer_type": record["answer_type"],
                "gold_doc_ids": record["gold_doc_ids"],
                "gold_evidence_spans": record["gold_evidence_spans"],
                "requires_refusal": requires_refusal,
                "unsupported_reason": record["unsupported_reason"],
                "notes": record.get("notes"),
                "split": split_name,
                "dataset": "medeval-v1",
                "not_clinically_validated": True,
            },
        )

    @staticmethod
    def _find_document_by_doc_id(db: Session, doc_id: str) -> Document | None:
        documents = db.execute(select(Document)).scalars().all()
        return next(
            (document for document in documents if document.metadata_json.get("doc_id") == doc_id),
            None,
        )

    @staticmethod
    def _resolve_span_chunk(
        document: Document | None, evidence_text: str, start_char: int, end_char: int
    ) -> DocumentChunk | None:
        if document is None:
            return None
        cleaned_evidence = text_cleaning_service.clean(evidence_text)
        for chunk in document.chunks:
            if cleaned_evidence and cleaned_evidence in chunk.chunk_text:
                return chunk
        for chunk in document.chunks:
            if chunk.char_start is None or chunk.char_end is None:
                continue
            if chunk.char_start <= start_char and end_char <= chunk.char_end:
                return chunk
        return document.chunks[0] if document.chunks else None


medeval_v1_seed_service = MedEvalV1SeedService()

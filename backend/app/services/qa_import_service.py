import json
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.qa_examples import EvidenceLinkCreate, EvidenceReference, QAExampleCreate
from app.services.dataset_service import dataset_service


@dataclass(frozen=True)
class QAImportResult:
    imported_examples: int
    evidence_links_created: int
    skipped_evidence_links: int


class QAImportService:
    def import_jsonl(self, db: Session, dataset_id: uuid.UUID, jsonl_text: str) -> QAImportResult:
        imported = 0
        links_created = 0
        links_skipped = 0

        for line_number, raw_line in enumerate(jsonl_text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}") from exc

            evidence_refs = (
                record.pop("evidence", None) or record.pop("required_evidence", None) or []
            )
            raw_chunk_ids = record.pop("required_evidence_chunk_ids", [])
            evidence_refs.extend(
                {"chunk_id": chunk_id, "evidence_role": "required"} for chunk_id in raw_chunk_ids
            )

            payload = QAExampleCreate(
                document_id=record.get("document_id"),
                question=record["question"],
                gold_answer=record["gold_answer"],
                answerability=record.get("answerability", "answerable"),
                category=record.get("category", "general"),
                difficulty=record.get("difficulty", "easy"),
                risk_level=record.get("risk_level", "low"),
                expected_behavior=record.get("expected_behavior"),
                reviewed_by_human=record.get("reviewed_by_human", False),
                metadata=record.get("metadata", {}),
            )
            example = dataset_service.create_qa_example(db, dataset_id, payload)
            imported += 1

            for evidence_record in evidence_refs:
                reference = EvidenceReference(**evidence_record)
                chunk = self.resolve_evidence_reference(db, reference)
                if chunk is None:
                    links_skipped += 1
                    continue
                dataset_service.create_evidence_link(
                    db,
                    example.id,
                    EvidenceLinkCreate(
                        chunk_id=chunk.id,
                        evidence_role=reference.evidence_role,
                        notes=reference.notes,
                    ),
                )
                links_created += 1

        return QAImportResult(imported, links_created, links_skipped)

    def export_jsonl(self, db: Session, dataset_id: uuid.UUID) -> str:
        examples = dataset_service.list_examples(db, dataset_id)
        lines = []
        for example in examples:
            evidence = [
                {
                    "chunk_id": str(link.chunk_id),
                    "evidence_role": link.evidence_role,
                    "notes": link.notes,
                }
                for link in example.evidence_links
            ]
            lines.append(
                json.dumps(
                    {
                        "question": example.question,
                        "gold_answer": example.gold_answer,
                        "answerability": example.answerability,
                        "category": example.category,
                        "difficulty": example.difficulty,
                        "risk_level": example.risk_level,
                        "document_id": str(example.document_id) if example.document_id else None,
                        "reviewed_by_human": example.reviewed_by_human,
                        "metadata": example.metadata_json,
                        "evidence": evidence,
                    }
                )
            )
        return "\n".join(lines) + ("\n" if lines else "")

    def resolve_evidence_reference(
        self, db: Session, reference: EvidenceReference
    ) -> DocumentChunk | None:
        if reference.chunk_id:
            return db.get(DocumentChunk, reference.chunk_id)
        if reference.chunk_index is None:
            return None

        statement = select(DocumentChunk).join(Document).where(
            DocumentChunk.chunk_index == reference.chunk_index
        )
        if reference.document_title:
            statement = statement.where(Document.title == reference.document_title)
        elif reference.document_file:
            statement = statement.where(
                Document.metadata_json["sample_file"].as_string().contains(reference.document_file)
            )
        else:
            return None
        return db.execute(statement).scalars().first()


qa_import_service = QAImportService()

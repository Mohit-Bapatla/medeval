import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.evidence_link import EvidenceLink
from app.models.qa_example import QAExample
from app.schemas.datasets import DatasetCreate
from app.schemas.qa_examples import EvidenceLinkCreate, QAExampleCreate


class DatasetService:
    def create_dataset(self, db: Session, payload: DatasetCreate) -> Dataset:
        dataset = Dataset(
            name=payload.name,
            description=payload.description,
            version=payload.version,
            source=payload.source,
            metadata_json=payload.metadata,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    def list_datasets(self, db: Session) -> list[Dataset]:
        return db.execute(select(Dataset).order_by(Dataset.created_at.desc())).scalars().all()

    def get_dataset(self, db: Session, dataset_id: uuid.UUID) -> Dataset | None:
        return db.get(Dataset, dataset_id)

    def delete_dataset(self, db: Session, dataset: Dataset) -> None:
        db.delete(dataset)
        db.commit()

    def create_qa_example(
        self, db: Session, dataset_id: uuid.UUID, payload: QAExampleCreate
    ) -> QAExample:
        example = QAExample(
            dataset_id=dataset_id,
            document_id=payload.document_id,
            question=payload.question,
            gold_answer=payload.gold_answer,
            answerability=payload.answerability,
            category=payload.category,
            difficulty=payload.difficulty,
            risk_level=payload.risk_level,
            expected_behavior=payload.expected_behavior,
            reviewed_by_human=payload.reviewed_by_human,
            metadata_json=payload.metadata,
        )
        db.add(example)
        db.commit()
        db.refresh(example)
        return example

    def list_examples(self, db: Session, dataset_id: uuid.UUID) -> list[QAExample]:
        return (
            db.execute(
                select(QAExample)
                .where(QAExample.dataset_id == dataset_id)
                .order_by(QAExample.created_at)
            )
            .scalars()
            .all()
        )

    def create_evidence_link(
        self, db: Session, qa_example_id: uuid.UUID, payload: EvidenceLinkCreate
    ) -> EvidenceLink:
        link = EvidenceLink(
            qa_example_id=qa_example_id,
            chunk_id=payload.chunk_id,
            evidence_role=payload.evidence_role,
            notes=payload.notes,
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    def list_evidence_links(self, db: Session, qa_example_id: uuid.UUID) -> list[EvidenceLink]:
        return (
            db.execute(
                select(EvidenceLink)
                .where(EvidenceLink.qa_example_id == qa_example_id)
                .order_by(EvidenceLink.created_at)
            )
            .scalars()
            .all()
        )


dataset_service = DatasetService()

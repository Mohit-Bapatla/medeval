import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.datasets import serialize_qa_example
from app.db.session import get_db
from app.models.qa_example import QAExample
from app.schemas.qa_examples import EvidenceLinkCreate, EvidenceLinkRead, QAExampleRead
from app.services.dataset_service import dataset_service

router = APIRouter(tags=["qa-examples"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/qa-examples/{qa_example_id}", response_model=QAExampleRead)
def get_qa_example(qa_example_id: uuid.UUID, db: DbSession) -> QAExampleRead:
    return serialize_qa_example(require_qa_example(db, qa_example_id))


@router.post(
    "/qa-examples/{qa_example_id}/evidence-links",
    response_model=EvidenceLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence_link(
    qa_example_id: uuid.UUID, payload: EvidenceLinkCreate, db: DbSession
) -> EvidenceLinkRead:
    require_qa_example(db, qa_example_id)
    return serialize_evidence_link(dataset_service.create_evidence_link(db, qa_example_id, payload))


@router.get("/qa-examples/{qa_example_id}/evidence-links", response_model=list[EvidenceLinkRead])
def list_evidence_links(qa_example_id: uuid.UUID, db: DbSession) -> list[EvidenceLinkRead]:
    require_qa_example(db, qa_example_id)
    return [
        serialize_evidence_link(link)
        for link in dataset_service.list_evidence_links(db, qa_example_id)
    ]


def require_qa_example(db: Session, qa_example_id: uuid.UUID) -> QAExample:
    example = db.get(QAExample, qa_example_id)
    if example is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QA example not found")
    return example


def serialize_evidence_link(link) -> EvidenceLinkRead:
    return EvidenceLinkRead(
        id=link.id,
        qa_example_id=link.qa_example_id,
        chunk_id=link.chunk_id,
        evidence_role=link.evidence_role,
        notes=link.notes,
        created_at=link.created_at,
    )

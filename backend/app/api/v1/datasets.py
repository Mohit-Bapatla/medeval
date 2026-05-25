import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.qa_example import QAExample
from app.schemas.datasets import DatasetCreate, DatasetImportResponse, DatasetRead
from app.schemas.qa_examples import QAExampleCreate, QAExampleRead
from app.services.dataset_service import dataset_service
from app.services.qa_import_service import qa_import_service

router = APIRouter(tags=["datasets"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/datasets", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: DbSession) -> DatasetRead:
    return serialize_dataset(dataset_service.create_dataset(db, payload))


@router.get("/datasets", response_model=list[DatasetRead])
def list_datasets(db: DbSession) -> list[DatasetRead]:
    return [serialize_dataset(dataset) for dataset in dataset_service.list_datasets(db)]


@router.get("/datasets/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: uuid.UUID, db: DbSession) -> DatasetRead:
    return serialize_dataset(require_dataset(db, dataset_id))


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: uuid.UUID, db: DbSession) -> None:
    dataset_service.delete_dataset(db, require_dataset(db, dataset_id))


@router.post("/datasets/{dataset_id}/examples", response_model=QAExampleRead, status_code=201)
def create_dataset_example(
    dataset_id: uuid.UUID, payload: QAExampleCreate, db: DbSession
) -> QAExampleRead:
    require_dataset(db, dataset_id)
    return serialize_qa_example(dataset_service.create_qa_example(db, dataset_id, payload))


@router.get("/datasets/{dataset_id}/examples", response_model=list[QAExampleRead])
def list_dataset_examples(dataset_id: uuid.UUID, db: DbSession) -> list[QAExampleRead]:
    require_dataset(db, dataset_id)
    examples = dataset_service.list_examples(db, dataset_id)
    return [serialize_qa_example(example) for example in examples]


@router.post("/datasets/{dataset_id}/import-jsonl", response_model=DatasetImportResponse)
async def import_dataset_jsonl(
    dataset_id: uuid.UUID,
    file: Annotated[UploadFile, File()],
    db: DbSession,
) -> DatasetImportResponse:
    require_dataset(db, dataset_id)
    content = await file.read()
    try:
        result = qa_import_service.import_jsonl(db, dataset_id, content.decode("utf-8"))
    except (UnicodeDecodeError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return DatasetImportResponse(
        dataset_id=dataset_id,
        imported_examples=result.imported_examples,
        evidence_links_created=result.evidence_links_created,
        skipped_evidence_links=result.skipped_evidence_links,
    )


@router.get("/datasets/{dataset_id}/export-jsonl")
def export_dataset_jsonl(dataset_id: uuid.UUID, db: DbSession) -> Response:
    require_dataset(db, dataset_id)
    return Response(
        content=qa_import_service.export_jsonl(db, dataset_id),
        media_type="application/x-ndjson",
    )


def require_dataset(db: Session, dataset_id: uuid.UUID) -> Dataset:
    dataset = dataset_service.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


def serialize_dataset(dataset: Dataset) -> DatasetRead:
    return DatasetRead(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version=dataset.version,
        source=dataset.source,  # type: ignore[arg-type]
        metadata=dataset.metadata_json,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


def serialize_qa_example(example: QAExample) -> QAExampleRead:
    return QAExampleRead(
        id=example.id,
        dataset_id=example.dataset_id,
        document_id=example.document_id,
        question=example.question,
        gold_answer=example.gold_answer,
        answerability=example.answerability,  # type: ignore[arg-type]
        category=example.category,
        difficulty=example.difficulty,  # type: ignore[arg-type]
        risk_level=example.risk_level,  # type: ignore[arg-type]
        expected_behavior=example.expected_behavior,
        reviewed_by_human=example.reviewed_by_human,
        metadata=example.metadata_json,
        created_at=example.created_at,
        updated_at=example.updated_at,
    )

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.chunks import ChunkingResponse, ChunkRead
from app.schemas.documents import (
    BulkEmbedRequest,
    DocumentChunkRequest,
    DocumentCreate,
    DocumentEmbedRequest,
    DocumentListItem,
    DocumentRead,
    EmbedResponse,
)
from app.services.chunking_service import chunking_service
from app.services.embedding_service import get_embedding_provider
from app.services.ingestion_service import ingestion_service

router = APIRouter(tags=["documents"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreate, db: DbSession) -> DocumentRead:
    document = ingestion_service.create_document(db, payload)
    return serialize_document(document)


@router.post("/documents/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File()],
    db: DbSession,
    title: Annotated[str | None, Form()] = None,
    source_type: Annotated[str, Form()] = "synthetic_demo",
    document_type: Annotated[str, Form()] = "unknown",
    organization_name: Annotated[str | None, Form()] = None,
    source_url: Annotated[str | None, Form()] = None,
) -> DocumentRead:
    try:
        raw_text = await ingestion_service.extract_upload_text(file)
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    payload = DocumentCreate(
        title=title or file.filename or "Uploaded document",
        source_url=source_url,
        source_type=source_type,
        organization_name=organization_name,
        document_type=document_type,
        raw_text=raw_text,
        metadata={"filename": file.filename, "content_type": file.content_type},
    )
    document = ingestion_service.create_document(db, payload)
    return serialize_document(document)


@router.get("/documents", response_model=list[DocumentListItem])
def list_documents(db: DbSession) -> list[DocumentListItem]:
    documents = db.execute(select(Document).order_by(Document.created_at.desc())).scalars().all()
    return [serialize_document_list_item(document) for document in documents]


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: uuid.UUID, db: DbSession) -> DocumentRead:
    return serialize_document(require_document(db, document_id))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: DbSession) -> None:
    document = require_document(db, document_id)
    db.delete(document)
    db.commit()


@router.post("/documents/{document_id}/chunk", response_model=ChunkingResponse)
def chunk_document(
    document_id: uuid.UUID,
    db: DbSession,
    payload: DocumentChunkRequest | None = None,
) -> ChunkingResponse:
    document = require_document(db, document_id)
    request = payload or DocumentChunkRequest()

    if request.replace_existing:
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        db.flush()

    text_chunks = chunking_service.chunk_text(
        document.cleaned_text,
        chunk_size_chars=request.chunk_size_chars,
        chunk_overlap_chars=request.chunk_overlap_chars,
        min_chunk_chars=request.min_chunk_chars,
    )
    chunks = [
        DocumentChunk(
            document_id=document.id,
            chunk_index=text_chunk.chunk_index,
            chunk_text=text_chunk.chunk_text,
            token_count=text_chunk.token_count,
            char_start=text_chunk.char_start,
            char_end=text_chunk.char_end,
            metadata_json={},
        )
        for text_chunk in text_chunks
    ]
    db.add_all(chunks)
    db.commit()
    for chunk in chunks:
        db.refresh(chunk)

    return ChunkingResponse(
        document_id=document.id,
        chunks_created=len(chunks),
        chunks=[serialize_chunk(chunk) for chunk in chunks],
    )


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkRead])
def list_document_chunks(document_id: uuid.UUID, db: DbSession) -> list[ChunkRead]:
    require_document(db, document_id)
    chunks = (
        db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        .scalars()
        .all()
    )
    return [serialize_chunk(chunk) for chunk in chunks]


@router.post("/documents/{document_id}/embed", response_model=EmbedResponse)
def embed_document_chunks(
    document_id: uuid.UUID,
    db: DbSession,
    payload: DocumentEmbedRequest | None = None,
) -> EmbedResponse:
    require_document(db, document_id)
    request = payload or DocumentEmbedRequest()
    chunks = (
        db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        .scalars()
        .all()
    )
    embedded = embed_chunks(chunks, force=request.force)
    db.commit()
    return EmbedResponse(
        embedded_chunks=embedded,
        embedding_model=get_embedding_provider().model_name,
        embedding_dimension=get_embedding_provider().dimension,
    )


@router.post("/chunks/embed", response_model=EmbedResponse)
def embed_missing_chunks(
    db: DbSession,
    payload: BulkEmbedRequest | None = None,
) -> EmbedResponse:
    request = payload or BulkEmbedRequest()
    statement = select(DocumentChunk).order_by(DocumentChunk.created_at)
    if not request.force:
        statement = statement.where(DocumentChunk.embedding.is_(None))
    if request.limit:
        statement = statement.limit(request.limit)

    chunks = db.execute(statement).scalars().all()
    embedded = embed_chunks(chunks, force=request.force)
    db.commit()
    provider = get_embedding_provider()
    return EmbedResponse(
        embedded_chunks=embedded,
        embedding_model=provider.model_name,
        embedding_dimension=provider.dimension,
    )


def embed_chunks(chunks: list[DocumentChunk], force: bool) -> int:
    provider = get_embedding_provider()
    to_embed = [chunk for chunk in chunks if force or chunk.embedding is None]
    vectors = provider.embed_texts([chunk.chunk_text for chunk in to_embed])
    for chunk, vector in zip(to_embed, vectors, strict=True):
        chunk.embedding = vector
        chunk.embedding_model = provider.model_name
    return len(to_embed)


def require_document(db: Session, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


def serialize_document(document: Document) -> DocumentRead:
    return DocumentRead(
        id=document.id,
        title=document.title,
        source_url=document.source_url,
        source_type=document.source_type,
        organization_name=document.organization_name,
        document_type=document.document_type,
        raw_text=document.raw_text,
        cleaned_text=document.cleaned_text,
        metadata=document.metadata_json,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def serialize_document_list_item(document: Document) -> DocumentListItem:
    return DocumentListItem(
        id=document.id,
        title=document.title,
        source_url=document.source_url,
        source_type=document.source_type,
        organization_name=document.organization_name,
        document_type=document.document_type,
        metadata=document.metadata_json,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def serialize_chunk(chunk: DocumentChunk) -> ChunkRead:
    return ChunkRead(
        id=chunk.id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        chunk_text=chunk.chunk_text,
        token_count=chunk.token_count,
        char_start=chunk.char_start,
        char_end=chunk.char_end,
        page_number=chunk.page_number,
        section_title=chunk.section_title,
        embedding_model=chunk.embedding_model,
        metadata=chunk.metadata_json,
        created_at=chunk.created_at,
    )

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prompt_template import PromptTemplate
from app.schemas.prompts import PromptTemplateCreate, PromptTemplateRead
from app.services.prompt_service import prompt_service

router = APIRouter(tags=["prompt-templates"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/prompt-templates",
    response_model=PromptTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_prompt_template(payload: PromptTemplateCreate, db: DbSession) -> PromptTemplateRead:
    return serialize_prompt(prompt_service.create_prompt_template(db, payload))


@router.get("/prompt-templates", response_model=list[PromptTemplateRead])
def list_prompt_templates(db: DbSession) -> list[PromptTemplateRead]:
    return [serialize_prompt(prompt) for prompt in prompt_service.list_prompt_templates(db)]


@router.get("/prompt-templates/{prompt_template_id}", response_model=PromptTemplateRead)
def get_prompt_template(prompt_template_id: uuid.UUID, db: DbSession) -> PromptTemplateRead:
    prompt = prompt_service.get_prompt_template(db, prompt_template_id)
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found",
        )
    return serialize_prompt(prompt)


def serialize_prompt(prompt: PromptTemplate) -> PromptTemplateRead:
    return PromptTemplateRead(
        id=prompt.id,
        name=prompt.name,
        version=prompt.version,
        template_text=prompt.template_text,
        template_type=prompt.template_type,  # type: ignore[arg-type]
        metadata=prompt.metadata_json,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )

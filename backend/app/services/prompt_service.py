import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate
from app.schemas.prompts import PromptTemplateCreate

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
DEFAULT_RAG_PROMPT_PATH = PROMPTS_DIR / "rag_answer_prompt.txt"


class PromptService:
    def create_prompt_template(self, db: Session, payload: PromptTemplateCreate) -> PromptTemplate:
        template = PromptTemplate(
            name=payload.name,
            version=payload.version,
            template_text=payload.template_text,
            template_type=payload.template_type,
            metadata_json=payload.metadata,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def get_prompt_template(self, db: Session, template_id: uuid.UUID) -> PromptTemplate | None:
        return db.get(PromptTemplate, template_id)

    def list_prompt_templates(self, db: Session) -> list[PromptTemplate]:
        return (
            db.execute(select(PromptTemplate).order_by(PromptTemplate.created_at.desc()))
            .scalars()
            .all()
        )

    def default_rag_template_text(self) -> str:
        return DEFAULT_RAG_PROMPT_PATH.read_text(encoding="utf-8")

    def render_rag_prompt(
        self, question: str, source_chunks: list[tuple[str, str]], template: str
    ) -> str:
        chunk_text = "\n\n".join(
            f"Chunk ID: {chunk_id}\n{chunk_content}" for chunk_id, chunk_content in source_chunks
        )
        return template.format(question=question, source_chunks=chunk_text)


prompt_service = PromptService()

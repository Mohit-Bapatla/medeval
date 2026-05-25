import uuid
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.prompt_template import PromptTemplate
from app.schemas.experiments import ExperimentCreate


class ExperimentConfig(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    dataset_id: uuid.UUID | None = None
    dataset_name: str | None = None
    description: str | None = None
    model_provider: str = "deterministic_local"
    model_name: str = "deterministic-extractive-answer-v1"
    embedding_model: str = "deterministic-hash-embedding-384"
    retrieval_strategy: str = "vector_similarity"
    top_k: int = Field(default=5, ge=1, le=50)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    prompt_template_id: uuid.UUID | None = None
    prompt_template_name: str | None = None
    prompt_template_version: str | None = None
    evaluator_version: str = "0.2.0"
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("dataset_name")
    @classmethod
    def require_dataset_reference(
        cls, value: str | None, info
    ) -> str | None:
        if not value and not info.data.get("dataset_id"):
            raise ValueError("dataset_id or dataset_name is required")
        return value


class ConfigService:
    def parse_experiment_yaml(self, yaml_text: str) -> ExperimentConfig:
        try:
            raw = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError as exc:
            raise ValueError("Invalid experiment YAML") from exc
        if not isinstance(raw, dict):
            raise ValueError("Experiment YAML must contain a mapping")
        return ExperimentConfig(**raw)

    def load_experiment_config(self, path: Path) -> ExperimentConfig:
        return self.parse_experiment_yaml(path.read_text(encoding="utf-8"))

    def to_experiment_create(self, db: Session, config: ExperimentConfig) -> ExperimentCreate:
        dataset_id = config.dataset_id or self._resolve_dataset_id(db, config.dataset_name)
        prompt_template_id = config.prompt_template_id
        if prompt_template_id is None and config.prompt_template_name:
            prompt_template_id = self._resolve_prompt_template_id(
                db,
                config.prompt_template_name,
                config.prompt_template_version,
            )
        metadata = {
            **config.metadata,
            "config_notes": config.notes,
            "evaluator_version": config.evaluator_version,
            "config_source": "yaml",
        }
        return ExperimentCreate(
            name=config.name,
            dataset_id=dataset_id,
            description=config.description,
            model_provider=config.model_provider,
            model_name=config.model_name,
            embedding_model=config.embedding_model,
            prompt_template_id=prompt_template_id,
            retrieval_strategy=config.retrieval_strategy,
            top_k=config.top_k,
            temperature=config.temperature,
            metadata=metadata,
        )

    def _resolve_dataset_id(self, db: Session, dataset_name: str | None) -> uuid.UUID:
        if not dataset_name:
            raise ValueError("dataset_id or dataset_name is required")
        dataset = (
            db.execute(select(Dataset).where(Dataset.name == dataset_name)).scalars().first()
        )
        if dataset is None:
            raise ValueError(f"Dataset not found for name: {dataset_name}")
        return dataset.id

    def _resolve_prompt_template_id(
        self, db: Session, name: str, version: str | None
    ) -> uuid.UUID:
        statement = select(PromptTemplate).where(PromptTemplate.name == name)
        if version:
            statement = statement.where(PromptTemplate.version == version)
        template = db.execute(statement).scalars().first()
        if template is None:
            raise ValueError(f"Prompt template not found for name: {name}")
        return template.id


config_service = ConfigService()

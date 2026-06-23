from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, StrictBool, model_validator

DatasetCategory = Literal[
    "eligibility",
    "required_documents",
    "deadlines",
    "step_by_step_process",
    "benefits_services",
    "restrictions_exclusions",
    "location_contact",
    "privacy_safety",
    "clinical_caution",
    "multi_hop",
    "ambiguous",
    "unsupported",
    "out_of_scope",
    "contradiction_sensitive",
    "temporal_versioned",
]

Difficulty = Literal["easy", "medium", "hard"]

AnswerType = Literal[
    "extractive",
    "abstractive",
    "list",
    "multi_hop",
    "refusal",
    "comparison",
    "temporal",
]

SourceType = Literal[
    "public_health_guidance",
    "patient_education",
    "federal_policy",
    "state_policy",
    "clinical_trial",
    "drug_device_safety",
    "insurance_program",
    "nonprofit_program",
    "synthetic_scenario",
]


class BenchmarkDocumentMetadata(BaseModel):
    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    source_type: SourceType
    source_url: HttpUrl
    accessed_at: date
    license_notes: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    difficulty: Difficulty
    document_path: str = Field(pattern=r"^documents/.+")


class BenchmarkLabelMetadata(BaseModel):
    qa_id: str = Field(min_length=1)
    reviewed: StrictBool = False
    reviewer_role: str | None = None
    notes: str | None = None


class EvidenceSpan(BaseModel):
    doc_id: str = Field(min_length=1)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "EvidenceSpan":
        if self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        return self


class BenchmarkQAExample(BaseModel):
    qa_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    answer_type: AnswerType
    expected_answer: str = Field(min_length=1)
    gold_doc_ids: list[str] = Field(default_factory=list)
    gold_evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    difficulty: Difficulty
    category: DatasetCategory
    requires_refusal: StrictBool = False
    unsupported_reason: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def evidence_and_refusal_must_match(self) -> "BenchmarkQAExample":
        if self.requires_refusal:
            if not self.unsupported_reason:
                raise ValueError("requires_refusal examples must include unsupported_reason")
            if self.answer_type != "refusal":
                raise ValueError("requires_refusal examples must use answer_type='refusal'")
        else:
            if self.unsupported_reason is not None:
                raise ValueError("answerable examples must not include unsupported_reason")
            if not self.gold_doc_ids:
                raise ValueError("answerable examples must include at least one gold_doc_id")
            if not self.gold_evidence_spans:
                raise ValueError("answerable examples must include at least one evidence span")
        return self

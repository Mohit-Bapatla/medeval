import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.datasets.schemas import (
    AnswerType,
    BenchmarkDocumentMetadata,
    BenchmarkLabelMetadata,
    BenchmarkQAExample,
    DatasetCategory,
    Difficulty,
    SourceType,
)

REQUIRED_DATASET_PATHS = [
    Path("README.md"),
    Path("documents"),
    Path("metadata/docs.json"),
    Path("qa/README.md"),
    Path("metadata/docs.example.json"),
    Path("metadata/labels.example.json"),
    Path("metadata/taxonomy.yaml"),
]

REAL_QA_FILES = [
    Path("qa/qa_eval.jsonl"),
    Path("qa/qa_hard.jsonl"),
    Path("qa/qa_refusal.jsonl"),
]

EXAMPLE_QA_FILES = [
    Path("qa/qa_eval.example.jsonl"),
    Path("qa/qa_hard.example.jsonl"),
    Path("qa/qa_refusal.example.jsonl"),
]

SENSITIVE_PLACEHOLDER_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\bMRN\s*[:#]", re.IGNORECASE),
    re.compile(r"\bDOB\s*[:#]", re.IGNORECASE),
    re.compile(r"\bmedical record number\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class DatasetValidationResult:
    dataset_path: Path
    documents: list[BenchmarkDocumentMetadata] = field(default_factory=list)
    example_documents: list[BenchmarkDocumentMetadata] = field(default_factory=list)
    qa_examples: list[BenchmarkQAExample] = field(default_factory=list)
    example_qa_examples: list[BenchmarkQAExample] = field(default_factory=list)
    qa_examples_by_split: dict[str, list[BenchmarkQAExample]] = field(default_factory=dict)
    labels: list[BenchmarkLabelMetadata] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_dataset(dataset_path: Path) -> DatasetValidationResult:
    root = dataset_path.resolve()
    errors: list[str] = []

    for required_path in REQUIRED_DATASET_PATHS:
        if not (root / required_path).exists():
            errors.append(f"Missing required path: {required_path}")
    for required_path in REAL_QA_FILES:
        if not (root / required_path).exists():
            errors.append(f"Missing required QA split: {required_path}")

    taxonomy = _load_taxonomy(root / "metadata" / "taxonomy.yaml", errors)
    _validate_taxonomy(taxonomy, errors)

    documents = _load_json_list(
        root / "metadata" / "docs.json",
        BenchmarkDocumentMetadata,
        errors,
        label="document metadata",
    )
    example_documents = _load_json_list(
        root / "metadata" / "docs.example.json",
        BenchmarkDocumentMetadata,
        errors,
        label="example document metadata",
    )
    labels = _load_json_list(
        root / "metadata" / "labels.example.json",
        BenchmarkLabelMetadata,
        errors,
        label="label metadata",
    )

    qa_examples_by_split: dict[str, list[BenchmarkQAExample]] = {}
    qa_examples: list[BenchmarkQAExample] = []
    for split_path in REAL_QA_FILES:
        split_examples = _load_qa_jsonl(root / split_path, errors)
        qa_examples_by_split[split_path.name] = split_examples
        qa_examples.extend(split_examples)

    example_qa_examples: list[BenchmarkQAExample] = []
    for split_path in EXAMPLE_QA_FILES:
        example_qa_examples.extend(_load_qa_jsonl(root / split_path, errors))

    _validate_unique_doc_ids(documents, errors, label="docs.json")
    _validate_unique_doc_ids(example_documents, errors, label="docs.example.json")
    real_doc_ids = {document.doc_id for document in documents}
    example_doc_ids = {document.doc_id for document in example_documents}
    overlapping_doc_ids = sorted(real_doc_ids & example_doc_ids)
    if overlapping_doc_ids:
        errors.append(
            "Real and example document metadata share doc_id values: "
            f"{', '.join(overlapping_doc_ids)}"
        )

    real_document_texts = _load_document_texts(root, documents, errors)
    example_document_texts = _load_document_texts(root, example_documents, errors)
    for document in [*documents, *example_documents]:
        if not (root / document.document_path).exists():
            errors.append(
                f"{document.doc_id}: document_path does not exist: {document.document_path}"
            )

    _validate_qa_examples(
        qa_examples,
        real_doc_ids,
        real_document_texts,
        errors,
        label="real QA",
    )
    _validate_qa_examples(
        example_qa_examples,
        example_doc_ids,
        example_document_texts,
        errors,
        label="example QA",
    )

    label_ids = [label.qa_id for label in labels]
    example_qa_ids = {example.qa_id for example in example_qa_examples}
    unknown_label_ids = sorted(set(label_ids) - example_qa_ids)
    if unknown_label_ids:
        errors.append(
            "labels.example.json references unknown qa_id values: "
            f"{', '.join(unknown_label_ids)}"
        )

    return DatasetValidationResult(
        dataset_path=root,
        documents=documents,
        example_documents=example_documents,
        qa_examples=qa_examples,
        example_qa_examples=example_qa_examples,
        qa_examples_by_split=qa_examples_by_split,
        labels=labels,
        errors=errors,
    )


def dataset_statistics(dataset_path: Path) -> dict[str, Any]:
    result = validate_dataset(dataset_path)
    categories = Counter(example.category for example in result.qa_examples)
    difficulties = Counter(example.difficulty for example in result.qa_examples)
    answer_types = Counter(example.answer_type for example in result.qa_examples)
    source_types = Counter(document.source_type for document in result.documents)
    refusal_count = sum(1 for example in result.qa_examples if example.requires_refusal)
    qa_count_by_split = {
        split_name: len(examples)
        for split_name, examples in sorted(result.qa_examples_by_split.items())
    }

    return {
        "dataset_path": str(result.dataset_path),
        "valid": result.ok,
        "errors": result.errors,
        "document_count": len(result.documents),
        "example_document_count": len(result.example_documents),
        "qa_count": len(result.qa_examples),
        "example_qa_count": len(result.example_qa_examples),
        "qa_count_by_split": qa_count_by_split,
        "label_count": len(result.labels),
        "refusal_count": refusal_count,
        "answerable_count": len(result.qa_examples) - refusal_count,
        "qa_count_by_category": dict(sorted(categories.items())),
        "qa_count_by_difficulty": dict(sorted(difficulties.items())),
        "qa_count_by_answer_type": dict(sorted(answer_types.items())),
        "categories": dict(sorted(categories.items())),
        "difficulties": dict(sorted(difficulties.items())),
        "answer_types": dict(sorted(answer_types.items())),
        "source_types": dict(sorted(source_types.items())),
    }


def _validate_unique_doc_ids(
    documents: list[BenchmarkDocumentMetadata], errors: list[str], label: str
) -> None:
    counts = Counter(document.doc_id for document in documents)
    duplicates = sorted(doc_id for doc_id, count in counts.items() if count > 1)
    if duplicates:
        errors.append(f"{label}: duplicate doc_id values: {', '.join(duplicates)}")


def _load_document_texts(
    root: Path, documents: list[BenchmarkDocumentMetadata], errors: list[str]
) -> dict[str, str]:
    texts: dict[str, str] = {}
    for document in documents:
        document_path = root / document.document_path
        if not document_path.exists():
            continue
        texts[document.doc_id] = document_path.read_text(encoding="utf-8")
    return texts


def _validate_qa_examples(
    examples: list[BenchmarkQAExample],
    doc_ids: set[str],
    document_texts: dict[str, str],
    errors: list[str],
    label: str,
) -> None:
    qa_id_counts = Counter(example.qa_id for example in examples)
    duplicate_qa_ids = sorted(qa_id for qa_id, count in qa_id_counts.items() if count > 1)
    if duplicate_qa_ids:
        errors.append(f"{label}: duplicate qa_id values: {', '.join(duplicate_qa_ids)}")

    for example in examples:
        _validate_no_sensitive_placeholders(example, errors)
        missing_doc_ids = sorted(set(example.gold_doc_ids) - doc_ids)
        if missing_doc_ids:
            errors.append(f"{example.qa_id}: unknown gold_doc_ids: {', '.join(missing_doc_ids)}")
        for span in example.gold_evidence_spans:
            if span.doc_id not in doc_ids:
                errors.append(
                    f"{example.qa_id}: evidence span references unknown doc_id {span.doc_id}"
                )
                continue
            document_text = document_texts.get(span.doc_id, "")
            if span.text not in document_text:
                errors.append(
                    f"{example.qa_id}: evidence text does not appear in document {span.doc_id}"
                )
                continue
            expected_text = document_text[span.start_char : span.end_char]
            if expected_text != span.text:
                errors.append(
                    f"{example.qa_id}: evidence offsets do not match text for document "
                    f"{span.doc_id}"
                )


def _validate_no_sensitive_placeholders(
    example: BenchmarkQAExample, errors: list[str]
) -> None:
    values = [
        example.question,
        example.expected_answer,
        example.notes or "",
        *(span.text for span in example.gold_evidence_spans),
    ]
    for value in values:
        for pattern in SENSITIVE_PLACEHOLDER_PATTERNS:
            if pattern.search(value):
                errors.append(f"{example.qa_id}: possible sensitive placeholder matched")
                return


def _load_taxonomy(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{path.relative_to(path.parents[1])}: invalid YAML: {exc}")
        return {}
    if not isinstance(content, dict):
        errors.append(f"{path.relative_to(path.parents[1])}: taxonomy must be a mapping")
        return {}
    return content


def _validate_taxonomy(taxonomy: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "categories": set(DatasetCategory.__args__),
        "difficulty_levels": set(Difficulty.__args__),
        "answer_types": set(AnswerType.__args__),
        "source_types": set(SourceType.__args__),
    }
    for key, expected_values in expected.items():
        raw_values = taxonomy.get(key, [])
        if not isinstance(raw_values, list):
            errors.append(f"taxonomy.yaml: {key} must be a list")
            continue
        missing = expected_values - set(raw_values)
        extra = set(raw_values) - expected_values
        if missing:
            errors.append(f"taxonomy.yaml: {key} missing values: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"taxonomy.yaml: {key} has unknown values: {', '.join(sorted(extra))}")


def _load_json_list(
    path: Path,
    schema: type[BenchmarkDocumentMetadata] | type[BenchmarkLabelMetadata],
    errors: list[str],
    label: str,
) -> list[Any]:
    if not path.exists():
        return []
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return []
    if not isinstance(content, list):
        errors.append(f"{path.name}: expected a list of {label} records")
        return []

    records = []
    for index, record in enumerate(content, start=1):
        try:
            records.append(schema.model_validate(record))
        except ValidationError as exc:
            errors.append(f"{path.name}[{index}]: {exc.errors()[0]['msg']}")
    return records


def _load_qa_jsonl(path: Path, errors: list[str]) -> list[BenchmarkQAExample]:
    examples = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{line_number}: invalid JSONL: {exc}")
            continue
        try:
            examples.append(BenchmarkQAExample.model_validate(record))
        except ValidationError as exc:
            errors.append(f"{path.name}:{line_number}: {exc.errors()[0]['msg']}")
    return examples

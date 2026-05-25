from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db import base as _base  # noqa: F401
from app.db.session import SessionLocal
from app.models.dataset import Dataset
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.qa_example import QAExample
from app.schemas.datasets import DatasetCreate
from app.schemas.documents import DocumentCreate
from app.services.chunking_service import chunking_service
from app.services.config_service import config_service
from app.services.dataset_service import dataset_service
from app.services.embedding_service import get_embedding_provider
from app.services.experiment_service import experiment_service
from app.services.ingestion_service import ingestion_service
from app.services.qa_import_service import qa_import_service
from app.services.report_export_service import report_export_service

app = typer.Typer(help="MedEval deterministic local development CLI.")


@app.command()
def status() -> None:
    """Check DB connectivity and print local object counts."""
    typer.echo("MedEval local CLI is configured.")
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"connect_timeout": 2}
            if settings.DATABASE_URL.startswith("postgresql")
            else {},
        )
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        with SessionLocal() as db:
            datasets = len(db.execute(select(Dataset)).scalars().all())
            documents = len(db.execute(select(Document)).scalars().all())
        typer.echo("Database: reachable")
        typer.echo(f"Documents: {documents}")
        typer.echo(f"Datasets: {datasets}")
    except SQLAlchemyError as exc:
        typer.echo(f"Database: unreachable ({exc.__class__.__name__})")
        typer.echo("Start Postgres with `docker compose up -d db` before seeding or running.")


@app.command("seed-docs")
def seed_docs(
    path: Annotated[
        Path,
        typer.Option(
            help="Directory containing synthetic sample Markdown/TXT documents.",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
) -> None:
    """Seed, chunk, and embed synthetic sample documents."""
    provider = get_embedding_provider()
    with SessionLocal() as db:
        created = 0
        skipped = 0
        for document_path in sorted(path.glob("*")):
            if document_path.suffix.lower() not in {".md", ".txt"}:
                continue
            sample_file = document_path.name
            existing = (
                db.execute(
                    select(Document).where(
                        Document.metadata_json["sample_file"].as_string().contains(sample_file)
                    )
                )
                .scalars()
                .first()
            )
            if existing:
                skipped += 1
                continue
            raw_text = document_path.read_text(encoding="utf-8")
            document = ingestion_service.create_document(
                db,
                DocumentCreate(
                    title=document_path.stem.replace("_", " ").title(),
                    source_type="synthetic_demo",
                    document_type=_document_type_for_path(document_path),
                    raw_text=raw_text,
                    metadata={"sample_file": sample_file, "synthetic": True},
                ),
            )
            chunks = []
            for text_chunk in chunking_service.chunk_text(document.cleaned_text):
                chunks.append(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=text_chunk.chunk_index,
                        chunk_text=text_chunk.chunk_text,
                        token_count=text_chunk.token_count,
                        char_start=text_chunk.char_start,
                        char_end=text_chunk.char_end,
                        embedding=provider.embed_text(text_chunk.chunk_text),
                        embedding_model=provider.model_name,
                        metadata_json={"sample_file": sample_file},
                    )
                )
            db.add_all(chunks)
            db.commit()
            created += 1
            typer.echo(f"Seeded {sample_file}: {len(chunks)} chunks")
    typer.echo(f"Documents seeded: {created}; skipped existing: {skipped}")


@app.command("seed-qa")
def seed_qa(
    dataset_name: Annotated[
        str,
        typer.Option(help="Dataset name to create or reuse."),
    ] = "MedEval HealthcareQA Sample",
    path: Annotated[
        Path,
        typer.Option(
            help="Synthetic QA JSONL path.",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = Path("../datasets/sample/qa/healthcare_qa_sample.jsonl"),
) -> None:
    """Seed synthetic QA examples into the configured database."""
    with SessionLocal() as db:
        dataset = (
            db.execute(select(Dataset).where(Dataset.name == dataset_name)).scalars().first()
        )
        if dataset is None:
            dataset = dataset_service.create_dataset(
                db,
                DatasetCreate(
                    name=dataset_name,
                    description="Fictional QA examples for local MedEval development.",
                    source="synthetic_demo",
                    metadata={"sample_file": str(path), "synthetic": True},
                ),
            )
        existing_example = (
            db.execute(select(QAExample).where(QAExample.dataset_id == dataset.id))
            .scalars()
            .first()
        )
        if existing_example is not None:
            typer.echo(
                f"Dataset {dataset.id} already has QA examples; skipping import. "
                "Use a fresh database or delete the dataset to reseed."
            )
            return
        result = qa_import_service.import_jsonl(db, dataset.id, path.read_text(encoding="utf-8"))
    typer.echo(
        f"Seeded dataset {dataset.id}: {result.imported_examples} examples, "
        f"{result.evidence_links_created} evidence links, "
        f"{result.skipped_evidence_links} skipped evidence links"
    )


@app.command("run-experiment")
def run_experiment(
    config: Annotated[
        Path,
        typer.Option(help="YAML experiment config path.", exists=True, file_okay=True),
    ],
) -> None:
    """Create and run a deterministic local experiment from YAML."""
    with SessionLocal() as db:
        experiment_config = config_service.load_experiment_config(config)
        experiment = experiment_service.create_experiment_from_config(db, experiment_config)
        examples, responses, evaluations = experiment_service.run_experiment(db, experiment)
        summary = experiment_service.aggregate_results(db, experiment.id)
    typer.echo(f"Experiment ID: {experiment.id}")
    typer.echo(
        f"Run complete: {examples} examples, {responses} responses, {evaluations} evaluations"
    )
    typer.echo(summary.model_dump_json(indent=2))


@app.command("export-report")
def export_report(
    experiment_id: Annotated[str, typer.Option(help="Experiment UUID.")],
    format: Annotated[
        str,
        typer.Option(help="Report format: markdown or json."),
    ] = "markdown",
    out: Annotated[Path, typer.Option(help="Output file path.")] = Path("../reports/report.md"),
) -> None:
    """Export a computed experiment report."""
    with SessionLocal() as db:
        report = report_export_service.build_report(db, _parse_uuid(experiment_id))
    out.parent.mkdir(parents=True, exist_ok=True)
    if format == "markdown":
        out.write_text(report["markdown"], encoding="utf-8")
    elif format == "json":
        out.write_text(_json_report(report), encoding="utf-8")
    else:
        raise typer.BadParameter("format must be markdown or json")
    typer.echo(f"Wrote {format} report to {out}")


@app.command("export-results")
def export_results(
    experiment_id: Annotated[str, typer.Option(help="Experiment UUID.")],
    format: Annotated[str, typer.Option(help="Results format: csv.")] = "csv",
    out: Annotated[Path, typer.Option(help="Output file path.")] = Path("../reports/results.csv"),
) -> None:
    """Export per-response experiment results."""
    if format != "csv":
        raise typer.BadParameter("format must be csv")
    with SessionLocal() as db:
        rows = report_export_service.response_rows(db, _parse_uuid(experiment_id))
        content = report_export_service.csv(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    typer.echo(f"Wrote CSV results to {out}")


def _document_type_for_path(path: Path) -> str:
    name = path.stem
    if "hipaa" in name:
        return "compliance_policy"
    if "onboarding" in name:
        return "onboarding_doc"
    if "shadowing" in name or "volunteer" in name:
        return "volunteer_listing"
    return "healthcare_opportunity"


def _parse_uuid(value: str):
    import uuid

    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise typer.BadParameter("experiment-id must be a UUID") from exc


def _json_report(report: dict) -> str:
    import json

    from fastapi.encoders import jsonable_encoder

    return json.dumps(jsonable_encoder(report), indent=2)

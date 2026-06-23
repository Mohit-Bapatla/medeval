# Experiment Configs

YAML experiment configs describe reproducible local experiment settings. The
included configs use deterministic local providers only. Some configs target
synthetic demo data, while `medeval_v1_deterministic.yaml` targets the
in-development MedEval v1 public healthcare seed dataset after it has been
seeded locally.

Example:

```yaml
name: Synthetic deterministic baseline v0.1
dataset_name: MedEval HealthcareQA Sample
model_provider: deterministic_local
model_name: deterministic-extractive-answer-v1
embedding_model: deterministic-hash-embedding-384
retrieval_strategy: vector_similarity
top_k: 5
temperature: 0.0
```

Run one locally:

```powershell
cd backend
.\.venv\Scripts\medeval run-experiment --config ..\configs\experiments\baseline_deterministic.yaml
```

Run the MedEval v1 deterministic seed config after seeding the dataset:

```bash
cd backend
medeval seed-dataset --path ../datasets/medeval-v1 --dataset-name "MedEval v1 Public Healthcare Seed"
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic.yaml
```

## Multi-Config Deterministic Comparisons

MedEval v1 includes deterministic local config variants for pipeline debugging
and regression testing. They compare retrieval context size, cleaned retrieved
context, and a metadata-assisted refusal control without using external model
APIs.

Available MedEval v1 configs:

- `medeval_v1_deterministic.yaml`: baseline top-5 deterministic run.
- `medeval_v1_deterministic_top3.yaml`: stricter top-3 retrieval context.
- `medeval_v1_deterministic_top8.yaml`: larger top-8 retrieval context.
- `medeval_v1_deterministic_clean_context.yaml`: strips YAML frontmatter and
  source metadata from retrieved context before deterministic answer generation.
- `medeval_v1_deterministic_refusal_aware.yaml`: metadata-assisted
  deterministic refusal oracle for examples marked `requires_refusal`.
- `medeval_v1_deterministic_top5_clean_refusal.yaml`: combines clean context
  with the metadata-assisted refusal control.

Example comparison workflow:

```bash
cd backend
medeval seed-dataset --path ../datasets/medeval-v1 --dataset-name "MedEval v1 Public Healthcare Seed"
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_top3.yaml
medeval run-experiment --config ../configs/experiments/medeval_v1_deterministic_clean_context.yaml
medeval compare-runs --experiment-id <baseline-id> --experiment-id <top3-id> --experiment-id <clean-id> --format markdown --out ../reports/medeval_v1_comparison_report.md
medeval compare-runs --experiment-id <baseline-id> --experiment-id <top3-id> --format json --out ../reports/medeval_v1_comparison_report.json
medeval compare-runs --experiment-id <baseline-id> --experiment-id <top3-id> --format csv --out ../reports/medeval_v1_comparison_results.csv
```

These comparisons are local deterministic debugging artifacts. They are not
clinical validation, medical advice, production readiness evidence, or a
validated model leaderboard.

Do not store provider keys, sensitive data, real patient data, private student
data, or fabricated benchmark results here.

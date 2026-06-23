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

Do not store provider keys, sensitive data, real patient data, private student
data, or fabricated benchmark results here.

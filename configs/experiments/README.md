# Experiment Configs

YAML experiment configs describe reproducible local experiment settings. The
included configs use synthetic datasets and deterministic local providers only.

Example:

```yaml
name: Synthetic deterministic baseline v0.1
dataset_name: Synthetic Healthcare Opportunity QA
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

Do not store provider keys, sensitive data, real patient data, private student
data, or fabricated benchmark results here.

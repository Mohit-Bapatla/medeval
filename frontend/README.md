# MedEval Frontend

Next.js app for the MedEval dashboard. Batch 3 includes overview, documents,
datasets, experiments, trace viewer, failure analysis, and report preview pages.

## Local Development

```powershell
npm install
npm run dev
```

The app expects the backend API at `http://localhost:8000/api/v1` unless
`NEXT_PUBLIC_API_BASE_URL` is set.

## Pages

- `/`: dashboard overview and local API status
- `/documents`: source documents and chunk details
- `/datasets`: QA datasets and examples
- `/experiments`: experiment list and run action
- `/experiments/[id]`: metrics, charts, and response table
- `/traces/[responseId]`: question, gold answer, model answer, retrieved chunks,
  citations, scores, and raw output
- `/failures`: failure analysis for a selected experiment
- `/reports`: report candidates
- `/experiments/[id]/report`: computed Markdown/JSON report preview

The frontend does not include auth or real provider keys. Empty states explain
how to seed synthetic sample data instead of hardcoding demo metrics.

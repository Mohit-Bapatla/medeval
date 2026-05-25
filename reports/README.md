# Reports

Generated reports can be written here during local development. Do not commit
fabricated benchmark results or reports containing sensitive data.

Batch 2 exposes aggregate experiment metrics through the API. Persisted report
exports are still deferred; any local report artifacts should remain generated
development output, not claimed validation.

Batch 3 adds computed report previews at
`GET /api/v1/experiments/{experiment_id}/report` and frontend report pages. The
reports include local aggregate metrics, failure examples, and limitations, but
they are not validated benchmark claims.

Batch 4 adds Markdown, JSON, and CSV export paths. Every generated report should
include limitations stating that synthetic sample data, deterministic providers,
and heuristic evaluators are not clinical validation or benchmark-grade evidence.

CLI examples:

```powershell
cd backend
.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format markdown --out ..\reports\example_report.md
.\.venv\Scripts\medeval export-report --experiment-id <experiment-id> --format json --out ..\reports\example_report.json
.\.venv\Scripts\medeval export-results --experiment-id <experiment-id> --format csv --out ..\reports\results.csv
```

Generated local report artifacts should normally remain uncommitted unless they
are clearly synthetic examples requested for documentation.

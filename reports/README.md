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

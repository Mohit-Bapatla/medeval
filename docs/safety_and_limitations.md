# Safety And Limitations

MedEval is an evaluation framework for healthcare RAG research and engineering.
It is not a medical device, diagnostic system, clinical decision support system,
or medical advice product.

MedEval outputs, reports, metrics, examples, and traces should not be used to
diagnose, treat, triage, or make decisions about individual patients. Any future
clinical use would require separate expert review, governance, validation,
monitoring, and regulatory analysis.

## Data Boundaries

- Do not use PHI.
- Do not use private patient records.
- Do not use private student data.
- Do not use confidential hospital, clinic, insurer, or organization records.
- Use public sources or clearly marked synthetic scenarios only.

## Current Limitations

- The current repository is early development software with synthetic local demo
  data and benchmark scaffolding.
- The MedEval v1 dataset has not yet been collected, reviewed, or clinically
  validated.
- Passing validation only means dataset files are structurally well formed.
- Existing deterministic evaluators are development heuristics, not clinical or
  benchmark-grade scoring.
- No adoption, clinical accuracy, safety, or benchmark performance claims should
  be inferred from this scaffold.


# Scripts

Utility scripts for local development and maintenance can be added here in later
batches.

## Seed Synthetic Documents

`seed_sample_documents.py` loads the fictional markdown files from
`datasets/sample/documents/`, chunks them, embeds them with the deterministic
local provider, and stores them in the configured database.

Run only after the database is available and migrations have been applied:

```powershell
python scripts/seed_sample_documents.py
```

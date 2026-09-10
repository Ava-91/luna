# Development

Luna is organized into focused modules:

- `scanner`: discovers files and coordinates local indexing
- `metadata`: reads, validates, and normalizes tags
- `artwork`: inspects embedded artwork and builds replacement plans
- `apply`: performs approved changes and records operations
- `cli`: command-line interface

Contributions should keep the review-first workflow and mutation boundaries intact.

## Validation

Run the development checks locally:

```bash
python -m unittest discover -s tests -v
python -m pytest -q
python -m ruff check src tests
python -m compileall -q src
```

CI covers Python 3.11–3.13, unittest/pytest, linting, compilation, dependency consistency, and security auditing.

The second remediation audit added regression coverage for metadata `None` clearing and rollback conflicts, artwork decoder and format-specific inspection behavior, filename-template validation, and scanner/index race handling. The current main branch is green across the configured CI checks.

## Real-world validation

A disposable 20-file library has also been used to validate the CLI against mixed MP3/M4A content, missing and whitespace-only metadata, Unicode filenames, valid embedded artwork, missing artwork, and invalid artwork payloads. Real metadata clearing and plan/inspection behavior were verified without unintended renames or repository changes.

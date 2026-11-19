# Changelog

## 1.0.0 — 2026-11-19

First stable release of Luna.

- Read-only-by-default scanning and metadata inspection for local music libraries.
- Exact and probable duplicate detection without automatic deletion.
- Embedded artwork auditing and reviewable replacement plans.
- Metadata normalization and collision-aware filename rename plans.
- Explicitly confirmed apply operations with JSON operation logs and rollback support.
- Library health reports and JSON, Markdown, and text exports.
- Optional SQLite indexing, configurable profiles, and a PySide6 desktop shell.
- Opt-in metadata-provider abstractions; the default workflow remains offline and local-first.
- Automated regression coverage and disposable-library integration/rollback validation.

## 0.2.0 — 2026-08-19

- Added recursive resilient audio scanning with richer metadata records and safe parallel reads.
- Added metadata validation and deterministic normalization plans.
- Added exact and probable duplicate detection without destructive actions.
- Added artwork audit, album grouping, and reviewable local-artwork replacement planning.
- Added cross-platform filename safety and collision-aware dry-run rename plans.
- Added explicit metadata/filename apply workflows with confirmation and rollback logs.
- Added library health reports and JSON/Markdown/text exports.
- Added optional SQLite indexing for incremental scans.
- Added configurable library profiles.
- Added provider abstraction with offline/local-only default behavior.
- Added optional PySide6 desktop shell.
- Added CI across Python 3.11–3.13, linting, tests, dependency checks, and security auditing.
- Added comprehensive regression coverage for scanner, normalization, planning, duplicates, and configuration.

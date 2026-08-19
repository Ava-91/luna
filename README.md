# 🌙 Luna

Luna is a **local-first music library cleaner** for messy metadata, artwork, filenames, and duplicates. It is terminal-first, read-only by default, and makes proposed changes reviewable before anything is written.

## Safety model

- Scanning, inspection, duplicate detection, artwork auditing, reports, and rename plans are read-only.
- Duplicate detection distinguishes exact byte matches from probable matches; Luna never deletes automatically.
- Write operations require an explicit `--confirm` flag and refuse to overwrite unrelated files.
- Rename and metadata operations can create a JSON operation log for rollback.
- External metadata providers are opt-in abstractions; the core remains offline/local-only.

## Install

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
```

Optional features: `pip install -e '.[desktop]'` for PySide6, `pip install -e '.[artwork]'` for Pillow, and `pip install -e '.[dev]'` for tests/linting.

## Commands

```text
luna scan PATH
luna inspect PATH
luna duplicates PATH
luna artwork PATH
luna artwork-plan PATH
luna normalize-plan PATH
luna rename-plan PATH
luna report PATH
luna export PATH OUTPUT.json
luna apply PATH --confirm --log .luna-operations.json
luna apply PATH --metadata --confirm --log .luna-operations.json
luna rollback .luna-operations.json --confirm
luna config show|set|reset
luna gui
```

## Supported formats and metadata

MP3, FLAC, M4A, AAC, OGG, Opus, WAV, and WMA are recognized by default. Mutagen reads title, artist, album, album artist, track/disc number, year, genre, and common raw tags. Missing, placeholder, malformed, and parser-error conditions are reported without modifying files.

## Workflows

`report` summarizes tracks, formats, metadata issues, exact duplicate groups, probable duplicates, estimated duplicate waste, artwork gaps, and filename proposals. `duplicates` never deletes. `artwork` is read-only; `artwork-plan` ranks local cover candidates without applying them. `normalize-plan` and `rename-plan` are dry runs. `apply` requires explicit confirmation and can be rolled back from its operation log.

The optional `LibraryIndex` stores local file timestamps, sizes, hashes, normalized metadata, and artwork state in SQLite so unchanged files can be recognized between scans. Profiles live under `~/.config/luna/config.json` by default and can define roots, extensions, ignored paths, worker count, and naming preferences.

`MetadataProvider` is a provider-independent interface with source/confidence-bearing candidates. `LocalOnlyProvider` is the default offline provider; network providers are never contacted implicitly.

The optional PySide6 UI provides folder selection, scan progress, a health summary, duplicate/rename counts, and an explicit read-only safety boundary. It reuses the same core modules as the CLI.

## Development and CI

```bash
pip install -e '.[dev]'
python -m unittest discover -s tests -v
python -m pytest -q
python -m ruff check src tests
python -m compileall -q src
```

CI covers Python 3.11–3.13, tests, linting, compilation, dependency consistency, and a dependency security audit. Tagged releases use `scripts/build_release.py` to produce reproducible sdist/wheel artifacts.

## Release

See `CHANGELOG.md` for the 0.2.0 release. Build locally with `python scripts/build_release.py`; tagged pushes run the release-build workflow.

## License

MIT

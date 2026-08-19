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
pip install -e .
```

Optional: `pip install -e '.[desktop]'` for PySide6, `pip install -e '.[artwork]'` for Pillow, and `pip install -e '.[dev]'` for pytest/Ruff.

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

## Features

MP3, FLAC, M4A, AAC, OGG, Opus, WAV, and WMA are recognized by default. Mutagen reads title, artist, album, album artist, track/disc number, year, genre, and common raw tags. Missing, placeholder, malformed, and parser-error conditions are reported without modifying files.

Exact duplicates are SHA-256 groups. Probable duplicates use conservative artist/title/file-property matching and carry confidence/reasons. No duplicate is ever deleted automatically.

Artwork auditing reports missing/invalid embedded artwork, MIME type, and dimensions when Pillow is available. Album grouping and deterministic local cover candidates make replacement proposals reviewable without applying them.

Normalization and rename plans preserve original values, Unicode, extensions, and safe cross-platform filenames while detecting collisions. Apply operations require explicit confirmation and can be reversed from their operation log, including metadata changes.

SQLite indexing stores timestamps, sizes, hashes, metadata, and artwork state locally. Profiles configure roots, extensions, ignored paths, worker count, and naming preferences. Metadata providers are source/confidence-bearing interfaces with an offline local-only default.

The optional PySide6 UI provides folder selection, progress, health summaries, duplicate counts, and rename counts while keeping the same read-only safety boundary.

## Development

```bash
pip install -e '.[dev]'
python -m unittest discover -s tests -v
python -m pytest -q
python -m ruff check src tests
python -m compileall -q src
```

CI covers Python 3.11–3.13, tests, linting, compilation, dependency consistency, and security auditing. `scripts/build_release.py` produces sdist/wheel artifacts and tagged pushes invoke the release-build workflow.

## Release

See `CHANGELOG.md` for 0.2.0 release notes.

## License

MIT

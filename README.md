# 🌙 Luna

Luna is a **local-first music library cleaner** for messy metadata, artwork, filenames, and duplicates. It is terminal-first, read-only by default, and makes proposed changes reviewable before anything is written.

## Current status

Luna 1.0.0 is the first stable release. The core workflows are covered by automated tests. Release validation includes a fresh disposable-library integration run, a rollback round trip, and clean-environment package installation and CLI smoke checks.

## Safety model

- Scanning, inspection, duplicate detection, artwork auditing, reports, and plans are read-only.
- Duplicate detection distinguishes exact byte matches from probable matches; Luna never deletes duplicates automatically.
- Write operations require explicit `--confirm` and refuse to overwrite unrelated files.
- Metadata changes, including clearing a value to `None`, are applied deliberately rather than silently converting `None` to the string `"None"`.
- Rename plans block files when required metadata is missing instead of inventing unsafe names.
- Rename and metadata operations can create a JSON operation log for rollback.
- External metadata providers are opt-in abstractions; the core remains offline/local-only.

## Install

```bash
python -m venv .venv
# Activate the virtual environment, then:
python -m pip install --upgrade pip
python -m pip install luna-music-manager==1.0.0
```

For development from a checkout:

```bash
python -m pip install -e '.[dev]'
```

Optional extras: `.[desktop]` installs PySide6 and `.[artwork]` installs Pillow.

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

`scan` discovers supported audio files and prints their basic metadata without running metadata validation. `inspect` performs metadata validation and reports validation issues for each discovered file. Both commands are read-only; use `--json` on `scan` and `--format json` on `inspect` for machine-readable output.

## Features

MP3, FLAC, M4A, AAC, OGG, Opus, WAV, and WMA are recognized by default. Mutagen reads title, artist, album, album artist, track/disc number, year, genre, and common raw tags. Missing, placeholder, malformed, and parser-error conditions are reported without modifying files.

Exact duplicates are SHA-256 groups. Probable duplicates use conservative artist/title/file-property matching and carry confidence/reasons. No duplicate is ever deleted automatically.

Artwork auditing reports missing or invalid embedded artwork, MIME type, and dimensions when Pillow is available. MP3 ID3 artwork and M4A `covr` artwork are inspected using format-specific handling. Album grouping and deterministic local cover candidates make replacement proposals reviewable without applying them.

Normalization and rename plans preserve original values, Unicode, extensions, and safe cross-platform filenames while detecting collisions. Invalid filename placeholders/templates are rejected by configuration validation, and plans block renames when required metadata is missing. Apply operations require explicit confirmation and can be reversed from their operation log, including metadata changes.

SQLite indexing stores timestamps, sizes, hashes, metadata, and artwork state locally. Profiles configure roots, extensions, ignored paths, worker count, and naming preferences. Metadata providers are source/confidence-bearing interfaces with an offline local-only default behavior.

The optional PySide6 UI provides folder selection, progress, health summaries, duplicate counts, and rename counts while keeping the same read-only safety boundary.

## Development

```bash
python -m pip install -e '.[dev]'
python -m unittest discover -s tests -v
python -m pytest -q
python -m ruff check src tests
python -m compileall -q src
python -m pip check
```

CI covers Python 3.11–3.13, unittest/pytest, linting, compilation, dependency consistency, and security auditing.

## Release

See [CHANGELOG.md](CHANGELOG.md) and [the v1.0.0 release notes](docs/releases/v1.0.0.md).

## License

MIT

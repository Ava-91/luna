# 🌙 Luna

Luna is a **local-first music library cleaner** for messy metadata, artwork, filenames, and duplicates. It is terminal-first, read-only by default, and makes proposed changes reviewable before anything is written.

## Current status

Luna is **v1 release-candidate ready**: the core workflows are implemented, the second remediation audit is complete, CI is green, and the application has been exercised against a disposable real-world music library containing mixed formats, missing metadata, unusual filenames, real embedded artwork, and invalid artwork data.

This status means the application is functioning and has strong automated and real-world validation. A final v1 release should still include a fresh end-to-end integration run, a final rollback run on a disposable library, and release/package sanity checks.

## Safety model

- Scanning, inspection, duplicate detection, artwork auditing, reports, and plans are read-only.
- Duplicate detection distinguishes exact byte matches from probable matches; Luna never deletes duplicates automatically.
- Write operations require explicit `--confirm` and refuse to overwrite unrelated files.
- Metadata changes, including clearing a value to `None`, are applied deliberately rather than silently converting `None` to the string `"None"`.
- Rename plans block files when required metadata is missing instead of inventing unsafe names.
- Rename and metadata operations can create a JSON operation log for rollback.
- External metadata providers are opt-in abstractions; the core remains offline/local-only.

## Real-world validation

A disposable 20-file library was used for end-to-end checks. It included MP3 and M4A files, missing and whitespace-only metadata, Unicode filenames, real embedded JPEG/PNG artwork, files without artwork, and an artwork entry whose payload was empty.

Observed behavior included:

- Metadata inspection correctly reported 6 affected tracks without modifying unrelated metadata.
- A whitespace-only Aurora album value was normalized to `None`, applied successfully, and verified as genuinely absent afterward. A second normalization plan returned `[]`, confirming no repeated change.
- MP3 and M4A artwork inspection correctly identified embedded artwork, dimensions, MIME types, and invalid/empty artwork payloads.
- Artwork planning grouped compatible tracks and returned no candidate when no safe local replacement existed.
- Rename planning generated metadata-based suggestions while blocking tracks missing required title/artist metadata.
- Configuration regression coverage passed 10/10 tests.

These checks complement the automated regression suite; they do not replace the final release smoke tests described above.

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

`scan` discovers supported audio files and prints their basic metadata without running metadata validation. `inspect` performs metadata validation and reports validation issues for each discovered file. Both commands are read-only; use `--json` on `scan` and `--format json` on `inspect` for machine-readable output.

## Features

MP3, FLAC, M4A, AAC, OGG, Opus, WAV, and WMA are recognized by default. Mutagen reads title, artist, album, album artist, track/disc number, year, genre, and common raw tags. Missing, placeholder, malformed, and parser-error conditions are reported without modifying files.

Exact duplicates are SHA-256 groups. Probable duplicates use conservative artist/title/file-property matching and carry confidence/reasons. No duplicate is ever deleted automatically.

Artwork auditing reports missing or invalid embedded artwork, MIME type, and dimensions when Pillow is available. MP3 ID3 artwork and M4A `covr` artwork are inspected using format-specific handling. Album grouping and deterministic local cover candidates make replacement proposals reviewable without applying them.

Normalization and rename plans preserve original values, Unicode, extensions, and safe cross-platform filenames while detecting collisions. Invalid filename placeholders/templates are rejected by configuration validation, and plans block renames when required metadata is missing. Apply operations require explicit confirmation and can be reversed from their operation log, including metadata changes.

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

CI covers Python 3.11–3.13, unittest/pytest, linting, compilation, dependency consistency, and security auditing. The current main branch is green across these checks. `scripts/build_release.py` produces sdist/wheel artifacts and tagged pushes invoke the release-build workflow.

## Release

The project is currently at **v1 release-candidate readiness**. See `CHANGELOG.md` for the 0.2.0 history and the latest validation notes.

Before publishing `v1.0.0`, run the final fresh-library integration workflow, perform one disposable-library rollback test, and verify the release artifacts in a clean environment.

## License

MIT

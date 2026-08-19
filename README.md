# 🌙 Luna

Luna is a **local-first music library cleaner** for messy metadata, artwork, filenames, and duplicates. It is terminal-first, read-only by default, and makes proposed changes reviewable before anything is written.

## Safety model

- Scanning, inspection, duplicate detection, artwork auditing, reports, and rename plans are read-only.
- Duplicate detection distinguishes exact byte matches from probable matches; Luna never deletes automatically.
- Write operations require an explicit `--confirm` flag and refuse to overwrite unrelated files.
- Rename operations can create a JSON operation log for rollback.
- External metadata providers are opt-in abstractions; the core remains offline/local-only.

## Install

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
```

Optional features:

```bash
pip install -e '.[desktop]'   # PySide6 shell
pip install -e '.[artwork]'   # Pillow dimensions/decoding
pip install -e '.[dev]'       # pytest + ruff
```

## Commands

```text
luna scan PATH
luna inspect PATH
luna duplicates PATH
luna artwork PATH
luna rename-plan PATH
luna report PATH
luna export PATH OUTPUT.json
luna apply PATH --confirm --log .luna-operations.json
luna rollback .luna-operations.json --confirm
luna config show|set|reset
luna gui
```

All inspection commands support deterministic JSON/text-oriented output where applicable. `rename-plan` is always a dry run. `apply` only executes the reviewed rename plan and requires explicit confirmation.

## Supported formats

MP3, FLAC, M4A, AAC, OGG, Opus, WAV, and WMA are recognized by default. Mutagen is used for common metadata fields including title, artist, album, album artist, track/disc number, year, and genre. Raw parsed metadata remains available on each scanned `Track` record for comparison.

## Workflows

### Library health

Run `luna report Music/` to see track count, formats, metadata problems, exact duplicate groups, estimated duplicate waste, missing artwork, and filename suggestions.

### Metadata

`inspect` validates missing and placeholder values. `normalize` rules are deterministic and conservative: whitespace/separator cleanup and track/disc number parsing preserve intentional punctuation and Unicode. Original values are retained in the plan.

### Duplicates

Exact duplicates are SHA-256 groups. Probable duplicates use conservative metadata/file-property matches and include a confidence score and reasons. No file is removed by duplicate detection.

### Artwork

`artwork` checks embedded artwork, image payload validity, MIME type, and dimensions when Pillow is installed. Album/album-artist grouping makes review easier. Local `cover`, `folder`, `front`, and `albumart` candidates can be ranked into a replacement plan without applying them.

### Rename/apply

`rename-plan` shows current and proposed paths, detects collisions, sanitizes platform-reserved names, preserves extensions, and keeps deterministic ordering. `apply --confirm` performs only reviewed safe renames and records reversible operations when a log path is supplied.

### SQLite index

The optional `LibraryIndex` stores file metadata, hashes, artwork state, and timestamps locally. Unchanged files can be recognized without rescanning their contents. The database is not required for basic CLI use.

### Providers

`MetadataProvider` and `MetadataCandidate` define a provider-independent interface. `LocalOnlyProvider` is the default offline implementation. Network providers can be added without coupling the scanner to an external service; candidates carry source and confidence and are never silently applied.

## Configuration

Luna stores a user-level profile under `~/.config/luna/config.json` by default. Configure roots, extensions, ignored paths, worker count, and naming preferences with `luna config`. A project can also pass an explicit profile to the Python API.

## Development

```bash
pip install -e '.[dev]'
python -m unittest discover -s tests -v
python -m pytest -q
python -m ruff check src tests
python -m compileall -q src
```

CI runs tests across Python 3.11–3.13, linting, compilation, dependency consistency, and a dependency security audit.

## Desktop UI

The PySide6 interface is intentionally thin: it reuses the same domain layer and does not bypass confirmation requirements. Install the optional desktop extra and run `luna gui`.

## Recovery

Before write operations, keep a normal backup of the music library. Luna's operation log records rename operations and can be passed to `luna rollback`. Rollback checks that changed files still exist and that original destinations are not occupied before moving anything.

## License

MIT

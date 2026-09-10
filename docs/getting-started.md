# Getting Started

Luna is a local-first music library cleaner. It is read-only by default: inspect your library and review plans before allowing any write operation.

## First scan

```bash
luna scan ~/Music
```

Scanning is read-only. Luna discovers supported audio files and reads their basic metadata without changing files.

## Inspect before changing anything

```bash
luna inspect ~/Music
luna normalize-plan ~/Music
luna artwork ~/Music
luna artwork-plan ~/Music
luna rename-plan ~/Music
```

Inspection and planning are read-only. Review the proposed changes before applying them.

## Safe workflow

1. Scan the library.
2. Inspect metadata, artwork, duplicates, and filenames as needed.
3. Review the generated plans.
4. Apply only the operation you intend, with explicit confirmation.
5. Verify the result.
6. Keep the operation log when you need rollback capability.

For example:

```bash
luna apply ~/Music --metadata --confirm --log .luna-operations.json
```

If a rollback is required, use the recorded operation log according to the rollback command documented in `docs/commands.md`.

## Real-world validation

The current v1 release candidate has been exercised on a disposable 20-file library containing mixed MP3/M4A files, missing metadata, whitespace-only metadata, Unicode filenames, real embedded artwork, files without artwork, and invalid artwork data. Metadata clearing, artwork inspection, planning behavior, and safety boundaries were verified without modifying the source repository or accidentally renaming the disposable test set.

A final v1 release should still receive a fresh end-to-end integration run, a disposable-library rollback run, and release/package smoke tests.

# Commands

## Scan
```bash
luna scan PATH
```
Read-only library scan. Use `--json` for machine-readable output.

## Inspect
```bash
luna inspect PATH
```
Validate metadata without modifying files. Use `--format json` for machine-readable output.

## Plans
```bash
luna normalize-plan PATH
luna rename-plan PATH
luna artwork-plan PATH
```
Generate reviewable normalization, filename, and artwork plans. Plans do not modify files.

## Duplicates
```bash
luna duplicates PATH
```
Find exact and probable duplicates. Luna does not delete duplicates automatically.

## Artwork
```bash
luna artwork PATH
```
Audit embedded artwork, including format-specific MP3/M4A artwork handling when available.

## Reports and export
```bash
luna report PATH
luna export PATH OUTPUT.json
```
Generate library health/report output or export structured data.

## Apply
```bash
luna apply PATH --metadata --confirm --log .luna-operations.json
luna apply PATH --confirm --log .luna-operations.json
```
Apply reviewed changes. Write operations require explicit `--confirm`.

## Rollback
```bash
luna rollback .luna-operations.json --confirm
```
Reverse logged operations when rollback is appropriate.

## Configuration
```bash
luna config show
luna config set ...
luna config reset ...
```
Inspect or manage library profiles and naming preferences. Use `luna config show` to inspect the current configuration before changing it.

## GUI
```bash
luna gui
```
Launch the optional PySide6 desktop shell.

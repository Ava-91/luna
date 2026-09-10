# Troubleshooting

## No files found

Check the path and supported extensions. Use `luna config show` to inspect the configured extensions and roots.

## Metadata issues remain

`luna inspect PATH` reports missing or invalid metadata without changing files. Run `luna normalize-plan PATH` to see whether Luna has a deterministic normalization proposal.

If the plan is empty (`[]`), there is currently no automatic normalization change to apply. Missing metadata may still be reported by inspection when there is not enough information to safely infer a value.

## Artwork is missing or invalid

Use:

```bash
luna artwork PATH
luna artwork-plan PATH
```

Luna distinguishes missing artwork from invalid embedded payloads when format-specific inspection and Pillow support are available. An artwork plan may have `candidate: null` when no safe local replacement candidate exists; this is not an error by itself.

## Rename plan blocks a file

A `blocked` rename with `Missing title or artist metadata.` means Luna intentionally refused to invent required filename components. Fix the metadata first or leave the file unchanged.

## Changes failed

Review the operation log and file permissions. Do not repeat a write operation blindly. Verify the file state first and use the recorded operation log when rollback is appropriate.

## Release testing

For final release validation, use a disposable library rather than a personal music collection. Confirm scan/plan read-only behavior before applying changes, verify the resulting metadata/filesystem state afterward, and perform rollback before considering the smoke test complete.

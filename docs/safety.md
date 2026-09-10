# Safety

Luna is designed to be safe by default and review-first.

## Luna does not

- Delete duplicates automatically
- Modify files during scans, inspection, or planning
- Overwrite unrelated files silently
- Touch files outside the selected library
- Turn a metadata `None` clear into the literal string `"None"`
- Generate rename operations when required title/artist metadata is missing

## Applying changes

Writing requires explicit confirmation:

```bash
luna apply PATH --confirm
```

For operations that need rollback capability, provide an operation log:

```bash
luna apply PATH --metadata --confirm --log .luna-operations.json
```

Operations can then be reviewed and rolled back using the recorded log.

## Validation status

The current release candidate has passed the second remediation audit, automated regression coverage, and real-world checks on a disposable 20-file library. Those real-world checks included metadata clearing, mixed MP3/M4A artwork inspection, invalid artwork payload detection, and safe rename planning.

A final v1 release still requires the release smoke-test checklist to be completed on a fresh disposable library and clean release environment.

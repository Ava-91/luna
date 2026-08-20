# Safety

Luna is designed to be safe by default.

## Luna does not

- Delete duplicates automatically
- Modify files during scans
- Overwrite files silently
- Touch files outside the selected library

## Applying changes

Writing requires explicit confirmation:

```bash
luna apply PATH --confirm
```

Operations can be logged and reviewed.

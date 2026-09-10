# Workflow

Luna follows a review-first workflow:

```text
SCAN -> ANALYZE -> PLAN -> REVIEW -> APPLY -> VERIFY
```

Plans are generated before modifications happen.

## Recommended release-safe workflow

1. **Scan** the target library.
2. **Analyze** metadata, duplicates, artwork, and filenames as needed.
3. **Plan** the intended changes.
4. **Review** the plan and make sure blocked or missing-data cases are understood.
5. **Apply** only the intended operation with explicit `--confirm`.
6. **Verify** the filesystem and metadata after the operation.
7. **Keep the operation log** when rollback may be needed.

## Verified behavior

Real-world testing on a disposable 20-file library confirmed that scanning and planning remain read-only, metadata clearing can remove a whitespace-only value without writing `"None"`, MP3/M4A artwork inspection handles valid and invalid embedded artwork, and rename planning blocks files that lack required metadata.

The second remediation audit also added regression coverage for metadata clearing/rollback behavior, artwork decoding/format inspection, filename-template validation, and scanner/index race handling.

## Release validation

The core workflow is release-candidate ready. Before publishing v1.0.0, repeat the complete workflow on a fresh disposable library, perform a rollback test, and verify packaged artifacts in a clean environment.

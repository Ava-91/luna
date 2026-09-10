# Configuration

View the active configuration with:

```bash
luna config show
```

Configuration controls scan behavior, supported extensions, ignored paths, worker count, library roots, and filename preferences.

The default filename template is:

```text
{track} - {artist} - {title}
```

Filename templates are validated before they are used for rename planning. Invalid or unsupported placeholders are rejected rather than being allowed to produce unsafe filenames.

Configuration changes should be reviewed before running a write operation. Scanning and planning remain read-only.

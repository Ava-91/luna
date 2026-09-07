from pathlib import Path


def resolve_mutation_path(root: Path, path: Path, *, reject_symlink: bool = True) -> Path:
    """Resolve a mutation target and require it to stay inside the library root."""
    root_resolved = root.expanduser().resolve()
    path = Path(path).expanduser()
    if reject_symlink and path.is_symlink():
        raise ValueError(f"Refusing to mutate symlinked path: {path}")
    resolved = path.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Mutation target is outside the selected library: {path}") from exc
    return resolved

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from datetime import datetime, timezone
import shutil

from .paths import resolve_mutation_path


@dataclass(frozen=True)
class Operation:
    action: str
    source: str
    destination: str
    timestamp: str
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    backup_path: str | None = None
    library_root: str | None = None


class OperationLog:
    def __init__(self, path: Path, library_root: Path | None = None):
        self.path = path
        self.library_root = library_root.expanduser().resolve() if library_root else None
        self.operations = []

    def record(self, action, source, destination, field=None, old_value=None, new_value=None, backup_path=None):
        self.operations.append(
            Operation(
                action,
                str(source),
                str(destination),
                datetime.now(timezone.utc).isoformat(),
                field,
                old_value,
                new_value,
                str(backup_path) if backup_path else None,
                str(self.library_root) if self.library_root else None,
            )
        )

    def record_metadata(self, path, field, old_value, new_value):
        self.record("metadata", path, path, field, old_value, new_value)

    def record_artwork(self, path, candidate, backup_path):
        self.record("artwork", path, candidate, backup_path=backup_path)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(x) for x in self.operations], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _load_operations(log_path: Path):
    data = json.loads(log_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Operation log must contain a JSON array.")
    required = {"action", "source", "destination", "timestamp"}
    operations = []
    for index, op in enumerate(data):
        if not isinstance(op, dict) or not required.issubset(op):
            raise ValueError(f"Invalid operation log entry at index {index}.")
        if op["action"] not in {"rename", "metadata", "artwork"}:
            raise ValueError(f"Unsupported operation at index {index}: {op['action']!r}.")
        if not isinstance(op["source"], str) or not isinstance(op["destination"], str):
            raise ValueError(f"Invalid paths in operation log entry at index {index}.")
        if op["action"] == "metadata" and not isinstance(op.get("field"), str):
            raise ValueError(f"Metadata operation at index {index} is missing a field.")
        if op["action"] == "artwork" and op.get("backup_path") is not None and not isinstance(op["backup_path"], str):
            raise ValueError(f"Artwork operation at index {index} has an invalid backup path.")
        if op.get("library_root") is not None and not isinstance(op["library_root"], str):
            raise ValueError(f"Invalid library root in operation log entry at index {index}.")
        operations.append(op)
    return operations


def _rollback_root(operations, root):
    if not operations:
        return None
    if root is not None:
        return Path(root).expanduser().resolve()
    roots = {op.get("library_root") for op in operations}
    if len(roots) != 1 or None in roots:
        raise ValueError("Rollback requires a selected library root or a log created with one.")
    return Path(next(iter(roots))).resolve()


def rollback(log_path: Path, confirm=False, root: Path | None = None):
    if not confirm:
        raise PermissionError("Rollback requires explicit confirmation (confirm=True).")

    operations = _load_operations(log_path)
    root = _rollback_root(operations, root)
    results = []
    for op in reversed(operations):
        if op["action"] == "metadata":
            try:
                from mutagen import File

                path = Path(op["source"])
                target = resolve_mutation_path(root, path)
                audio = File(target, easy=True)
                if audio is None:
                    raise OSError("Audio file could not be parsed.")
                if audio.tags is None:
                    audio.add_tags()
                if op["old_value"] is None:
                    audio.tags.pop(op["field"], None)
                else:
                    audio.tags[op["field"]] = [op["old_value"]]
                audio.save()
                results.append((True, str(path), op["field"]))
            except Exception as exc:
                results.append((False, str(op["source"]), str(exc)))
            continue

        if op["action"] == "artwork":
            backup_path = op.get("backup_path")
            source = Path(op["source"])
            if not backup_path:
                results.append((False, str(source), "Artwork rollback requires a backup created by the current apply workflow."))
                continue
            backup = Path(backup_path)
            if not backup.is_file():
                results.append((False, str(source), "Artwork backup is missing."))
                continue
            try:
                target = resolve_mutation_path(root, source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
                results.append((True, str(source), str(backup)))
            except (OSError, ValueError) as exc:
                results.append((False, str(source), str(exc)))
            continue

        try:
            src = Path(op["destination"])
            dst = Path(op["source"])
            resolved_src = resolve_mutation_path(root, src)
            resolved_dst = resolve_mutation_path(root, dst)
        except ValueError as exc:
            results.append((False, str(op["destination"]), str(exc)))
            continue
        if not resolved_src.exists():
            results.append((False, str(src), "Changed file is missing."))
            continue
        if resolved_dst.exists():
            results.append((False, str(src), "Original destination already exists."))
            continue
        try:
            resolved_src.rename(resolved_dst)
            results.append((True, str(src), str(dst)))
        except OSError as exc:
            results.append((False, str(src), str(exc)))
    return results

from dataclasses import asdict, dataclass, replace
from pathlib import Path
import json
from datetime import datetime, timezone
import os
import shutil
from uuid import uuid4

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
    status: str = "pending"


class OperationLog:
    def __init__(self, path: Path, library_root: Path | None = None):
        self.path = path
        self.library_root = library_root.expanduser().resolve() if library_root else None
        self.transaction_id = uuid4().hex
        self.state = "prepared"
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
        return len(self.operations) - 1

    def record_metadata(self, path, field, old_value, new_value):
        return self.record("metadata", path, path, field, old_value, new_value)

    def record_artwork(self, path, candidate, backup_path):
        return self.record("artwork", path, candidate, backup_path=backup_path)

    def mark_completed(self, index):
        self.operations[index] = replace(self.operations[index], status="completed")
        self.save()

    def finalize(self):
        self.state = "committed"
        self.save()

    def abort(self):
        self.state = "rolled_back"
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "transaction_id": self.transaction_id,
            "state": self.state,
            "library_root": str(self.library_root) if self.library_root else None,
            "operations": [asdict(x) for x in self.operations],
        }
        temporary = self.path.with_name(f".{self.path.name}.tmp-{uuid4().hex}")
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        try:
            with temporary.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            try:
                directory_fd = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        finally:
            if temporary.exists():
                temporary.unlink()


def _load_log(log_path: Path):
    data = json.loads(log_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        operations = []
        for op in data:
            if not isinstance(op, dict):
                raise ValueError("Invalid operation log entry.")
            operations.append({**op, "status": "completed"})
        return {"version": 1, "state": "committed", "library_root": None, "operations": operations}
    if not isinstance(data, dict) or not isinstance(data.get("operations"), list):
        raise ValueError("Operation log must contain a JSON array or transaction object.")
    required = {"action", "source", "destination", "timestamp"}
    for index, op in enumerate(data["operations"]):
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
        if op.get("status", "pending") not in {"pending", "completed"}:
            raise ValueError(f"Invalid operation status at index {index}.")
    return data


def _load_operations(log_path: Path):
    return _load_log(log_path)["operations"]


def _rollback_root(log, root):
    operations = log["operations"]
    if not operations:
        return None
    if root is not None:
        return Path(root).expanduser().resolve()
    logged_root = log.get("library_root")
    roots = {op.get("library_root") or logged_root for op in operations}
    if len(roots) != 1 or None in roots:
        raise ValueError("Rollback requires a selected library root or a log created with one.")
    return Path(next(iter(roots))).resolve()


def _rollback_rename_group(operations, root):
    completed = [op for op in operations if op.get("status", "completed") == "completed"]
    if not completed:
        return []
    resolved = []
    current_paths = set()
    for op in completed:
        current = resolve_mutation_path(root, Path(op["destination"]))
        original = resolve_mutation_path(root, Path(op["source"]))
        resolved.append((op, current, original))
        current_paths.add(current)

    for _, current, _ in resolved:
        if not current.exists():
            return [(False, str(current), "Changed file is missing.") for _, current, _ in resolved]
    for _, _, original in resolved:
        if original.exists() and original not in current_paths:
            return [(False, str(original), "Original destination already exists.")]

    staged = []
    try:
        for op, current, _ in resolved:
            temporary = current.with_name(f".{current.name}.luna-rollback-{uuid4().hex}")
            current.rename(temporary)
            staged.append((op, current, temporary))
        restored = []
        for (op, _, original), (_, _, temporary) in zip(resolved, staged):
            temporary.rename(original)
            restored.append((True, str(Path(op["destination"])), str(Path(op["source"]))))
        return list(reversed(restored))
    except OSError as exc:
        recovery_errors = []
        for _, current, temporary in reversed(staged):
            if temporary.exists():
                try:
                    temporary.rename(current)
                except OSError as recovery_exc:
                    recovery_errors.append(f"{temporary} -> {current}: {recovery_exc}")
        detail = f": {exc}"
        if recovery_errors:
            detail += "; recovery incomplete: " + "; ".join(recovery_errors)
        return [(False, str(op["destination"]), f"Rename rollback failed{detail}") for op in operations]


def rollback(log_path: Path, confirm=False, root: Path | None = None):
    if not confirm:
        raise PermissionError("Rollback requires explicit confirmation (confirm=True).")

    log = _load_log(log_path)
    operations = log["operations"]
    root = _rollback_root(log, root)
    results = []
    index = len(operations) - 1
    while index >= 0:
        op = operations[index]
        if op["action"] == "rename":
            end = index
            while index >= 0 and operations[index]["action"] == "rename":
                index -= 1
            group = operations[index + 1 : end + 1]
            try:
                results.extend(_rollback_rename_group(group, root))
            except ValueError as exc:
                results.extend((False, str(item["destination"]), str(exc)) for item in group)
            continue
        if op.get("status", "completed") != "completed":
            index -= 1
            continue
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
            index -= 1
            continue
        if op["action"] == "artwork":
            backup_path = op.get("backup_path")
            source = Path(op["source"])
            if not backup_path:
                results.append((False, str(source), "Artwork rollback requires a backup created by the current apply workflow."))
                index -= 1
                continue
            backup = Path(backup_path)
            if not backup.is_file():
                results.append((False, str(source), "Artwork backup is missing."))
                index -= 1
                continue
            try:
                target = resolve_mutation_path(root, source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
                results.append((True, str(source), str(backup)))
            except (OSError, ValueError) as exc:
                results.append((False, str(source), str(exc)))
            index -= 1
            continue
    return results

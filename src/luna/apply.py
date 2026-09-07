from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .planner import RenamePlanItem, validate_plan
from .backup import OperationLog
from .paths import resolve_mutation_path


@dataclass(frozen=True)
class AppliedChange:
    source: Path
    destination: Path
    success: bool
    error: str | None = None


def _temporary_path(source: Path, reserved: set[Path]) -> Path:
    while True:
        candidate = source.with_name(f".{source.name}.luna-tmp-{uuid4().hex}")
        if candidate not in reserved and not candidate.exists():
            reserved.add(candidate)
            return candidate


def apply_rename_plan(plan: list[RenamePlanItem], confirm: bool = False, log_path: Path | None = None, root: Path | None = None) -> list[AppliedChange]:
    if not confirm:
        raise PermissionError("Applying changes requires explicit confirmation (confirm=True).")
    if root is None:
        raise ValueError("Applying renames requires the selected library root.")
    root = root.expanduser().resolve()
    errors = validate_plan(plan)
    if errors:
        raise ValueError("Invalid rename plan: " + "; ".join(errors))

    changes = [item for item in plan if item.destination is not None and item.status == "change"]
    if not changes:
        return []

    source_paths = set()
    resolved_items = {}
    seen_sources = set()
    for item in changes:
        try:
            source = resolve_mutation_path(root, item.source)
            destination = resolve_mutation_path(root, item.destination)
        except ValueError as exc:
            return [AppliedChange(change.source, change.destination, False, str(exc)) for change in changes]
        if source in seen_sources:
            raise ValueError(f"Invalid rename plan: duplicate source: {item.source}")
        seen_sources.add(source)
        source_paths.add(source)
        resolved_items[item] = (source, destination)
        if not source.exists():
            return [AppliedChange(change.source, change.destination, False, "Rename plan is stale: source no longer exists.") for change in changes]

    for item in changes:
        _, destination = resolved_items[item]
        if destination.exists() and destination not in source_paths:
            return [AppliedChange(change.source, change.destination, False, f"Destination already exists: {change.destination}") for change in changes]

    log = OperationLog(log_path, root) if log_path else None
    reserved = source_paths | {destination for _, destination in resolved_items.values()}
    temporary = {}
    completed = []

    try:
        for item in changes:
            source, _ = resolved_items[item]
            temp = _temporary_path(source, reserved)
            source.rename(temp)
            temporary[item] = temp

        for item in changes:
            _, destination = resolved_items[item]
            temp = temporary[item]
            temp.rename(destination)
            completed.append(item)
    except OSError as exc:
        recovery_errors = []
        for item in reversed(completed):
            source, destination = resolved_items[item]
            try:
                destination.rename(source)
            except OSError as recovery_exc:
                recovery_errors.append(f"{destination} -> {source}: {recovery_exc}")
        for item in changes:
            source, _ = resolved_items[item]
            temp = temporary.get(item)
            if temp is not None and temp.exists():
                try:
                    temp.rename(source)
                except OSError as recovery_exc:
                    recovery_errors.append(f"{temp} -> {source}: {recovery_exc}")

        if recovery_errors:
            detail = "; ".join(recovery_errors)
            raise RuntimeError(f"Rename failed and recovery was incomplete: {detail}") from exc

        return [AppliedChange(item.source, item.destination, False, f"Rename transaction rolled back after failure: {exc}" if item not in completed else "Rename transaction rolled back after failure.") for item in changes]

    if log:
        for item in completed:
            source, destination = resolved_items[item]
            log.record("rename", source, destination)
        log.save()

    return [AppliedChange(item.source, item.destination, True) for item in completed]

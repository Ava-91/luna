from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .planner import RenamePlanItem, validate_plan
from .backup import OperationLog


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


def apply_rename_plan(plan: list[RenamePlanItem], confirm: bool = False, log_path: Path | None = None) -> list[AppliedChange]:
    if not confirm:
        raise PermissionError("Applying changes requires explicit confirmation (confirm=True).")
    errors = validate_plan(plan)
    if errors:
        raise ValueError("Invalid rename plan: " + "; ".join(errors))

    changes = [item for item in plan if item.destination is not None and item.status == "change"]
    if not changes:
        return []

    source_paths = {item.source.resolve() for item in changes}
    seen_sources = set()
    for item in changes:
        source = item.source.resolve()
        if source in seen_sources:
            raise ValueError(f"Invalid rename plan: duplicate source: {item.source}")
        seen_sources.add(source)
        if not item.source.exists():
            return [
                AppliedChange(change.source, change.destination, False, "Rename plan is stale: source no longer exists.")
                for change in changes
            ]

    for item in changes:
        destination = item.destination.resolve()
        if destination.exists() and destination not in source_paths:
            return [
                AppliedChange(change.source, change.destination, False, f"Destination already exists: {change.destination}")
                for change in changes
            ]

    log = OperationLog(log_path) if log_path else None
    reserved = source_paths | {item.destination.resolve() for item in changes}
    temporary = {}
    completed = []

    try:
        for item in changes:
            temp = _temporary_path(item.source, reserved)
            item.source.rename(temp)
            temporary[item.source] = temp

        for item in changes:
            temp = temporary[item.source]
            temp.rename(item.destination)
            completed.append(item)
    except OSError as exc:
        recovery_errors = []
        for item in reversed(completed):
            try:
                item.destination.rename(item.source)
            except OSError as recovery_exc:
                recovery_errors.append(f"{item.destination} -> {item.source}: {recovery_exc}")
        for item in changes:
            temp = temporary.get(item.source)
            if temp is not None and temp.exists():
                try:
                    temp.rename(item.source)
                except OSError as recovery_exc:
                    recovery_errors.append(f"{temp} -> {item.source}: {recovery_exc}")

        if recovery_errors:
            detail = "; ".join(recovery_errors)
            raise RuntimeError(f"Rename failed and recovery was incomplete: {detail}") from exc

        return [
            AppliedChange(
                item.source,
                item.destination,
                False,
                f"Rename transaction rolled back after failure: {exc}" if item not in completed else "Rename transaction rolled back after failure.",
            )
            for item in changes
        ]

    if log:
        for item in completed:
            log.record("rename", item.source, item.destination)
        log.save()

    return [AppliedChange(item.source, item.destination, True) for item in completed]

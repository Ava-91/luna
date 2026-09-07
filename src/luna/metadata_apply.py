from dataclasses import dataclass
from pathlib import Path
from mutagen import File
from .backup import OperationLog
from .normalize import normalize_track
from .paths import resolve_mutation_path


@dataclass(frozen=True)
class MetadataChange:
    path: Path
    field: str
    old: str | None
    new: str


def build_metadata_plan(tracks):
    return [
        MetadataChange(track.path, item.field, item.original, item.normalized)
        for track in tracks
        for item in normalize_track(track)
        if item.changed and item.normalized is not None
    ]


def apply_metadata_plan(plan, confirm=False, log_path=None, root: Path | None = None):
    if not confirm:
        raise PermissionError("Applying metadata changes requires explicit confirmation (confirm=True).")
    if root is None:
        raise ValueError("Applying metadata changes requires the selected library root.")

    root = root.expanduser().resolve()
    log = OperationLog(log_path, root) if log_path and plan else None
    log_indices = {}
    valid_items = []
    results = []
    for item in plan:
        try:
            target = resolve_mutation_path(root, item.path)
            valid_items.append((item, target))
            if log:
                log_indices[item] = log.record_metadata(target, item.field, item.old, item.new)
        except ValueError as exc:
            results.append((item, False, str(exc)))

    if log and valid_items:
        log.save()

    for item, target in valid_items:
        try:
            audio = File(target, easy=True)
            if audio is None:
                raise OSError("Audio file could not be parsed.")
            if audio.tags is None:
                audio.add_tags()
            audio.tags[item.field] = [item.new]
            audio.save()
            if log:
                log.mark_completed(log_indices[item])
            results.append((item, True, None))
        except Exception as exc:
            results.append((item, False, str(exc)))

    valid_item_set = {item for item, _ in valid_items}
    if log and valid_items and all(ok for item, ok, _ in results if item in valid_item_set):
        log.finalize()
    return results

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
    if log:
        for item in plan:
            target = resolve_mutation_path(root, item.path)
            log_indices[item] = log.record_metadata(target, item.field, item.old, item.new)
        log.save()

    results = []
    for item in plan:
        try:
            target = resolve_mutation_path(root, item.path)
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

    if log and all(ok for _, ok, _ in results):
        log.finalize()
    return results

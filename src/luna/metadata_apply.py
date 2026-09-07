from dataclasses import dataclass
from pathlib import Path
from mutagen import File
from .backup import OperationLog
from .normalize import normalize_track


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


def apply_metadata_plan(plan, confirm=False, log_path=None):
    if not confirm:
        raise PermissionError("Applying metadata changes requires explicit confirmation (confirm=True).")

    log = OperationLog(log_path) if log_path else None
    results = []
    for item in plan:
        try:
            # Use Mutagen's easy interface for both reading and writing logical
            # fields (title, artist, album, etc.). This keeps the writer aligned
            # with scanner.py, which reads with File(..., easy=True), and avoids
            # assigning EasyID3 names directly to native ID3 frame mappings.
            audio = File(item.path, easy=True)
            if audio is None:
                raise OSError("Audio file could not be parsed.")
            if audio.tags is None:
                audio.add_tags()
            audio[item.field] = [item.new]
            audio.save()
            if log:
                log.record_metadata(item.path, item.field, item.old, item.new)
            results.append((item, True, None))
        except Exception as exc:
            results.append((item, False, str(exc)))

    if log:
        log.save()
    return results

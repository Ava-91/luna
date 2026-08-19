from dataclasses import dataclass
import re
from .scanner import Track

@dataclass(frozen=True)
class NormalizedValue:
    field: str
    original: str | None
    normalized: str | None
    changed: bool

def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value.strip())
    value = re.sub(r"\s*([|])\s*", r" \1 ", value)
    value = re.sub(r" {2,}", " ", value).strip()
    return value or None

def normalize_track(track: Track) -> tuple[NormalizedValue, ...]:
    fields = ("title", "artist", "album", "album_artist", "genre")
    return tuple(NormalizedValue(f, getattr(track, f, None), normalize_text(getattr(track, f, None)), getattr(track, f, None) != normalize_text(getattr(track, f, None))) for f in fields)

def normalize_track_number(value: str | int | None) -> int | None:
    if value is None: return None
    try: return int(str(value).split("/", 1)[0].strip())
    except ValueError: return None

def normalize_disc_number(value: str | int | None) -> int | None:
    return normalize_track_number(value)

def normalization_plan(tracks):
    return [item for track in tracks for item in normalize_track(track) if item.changed]

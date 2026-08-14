from dataclasses import dataclass
from pathlib import Path

from mutagen import File

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".wma"}


@dataclass(frozen=True)
class Track:
    path: Path
    title: str | None
    artist: str | None
    album: str | None


def scan_library(root: Path) -> list[Track]:
    """Scan audio files without modifying anything on disk."""
    tracks: list[Track] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        audio = File(path, easy=True)
        tags = audio.tags if audio is not None else None

        tracks.append(
            Track(
                path=path,
                title=_first(tags, "title"),
                artist=_first(tags, "artist"),
                album=_first(tags, "album"),
            )
        )

    return tracks


def _first(tags: object, key: str) -> str | None:
    if tags is None or not hasattr(tags, "get"):
        return None
    value = tags.get(key)
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value) if value is not None else None

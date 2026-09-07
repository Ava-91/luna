from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from mutagen import File


@dataclass(frozen=True)
class ArtworkEntry:
    index: int
    mime: str | None
    width: int | None
    height: int | None
    valid: bool
    reason: str | None = None


@dataclass(frozen=True)
class ArtworkInfo:
    path: Path
    has_artwork: bool
    mime: str | None = None
    width: int | None = None
    height: int | None = None
    valid: bool = True
    reason: str | None = None
    entries: tuple[ArtworkEntry, ...] = ()


def _inspect_picture(index: int, picture) -> ArtworkEntry:
    data = bytes(getattr(picture, "data", b""))
    mime = getattr(picture, "mime", None)
    if not data:
        return ArtworkEntry(index, mime, None, None, False, "Artwork payload is empty.")

    width = height = None
    try:
        from PIL import Image
        from io import BytesIO
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
    except ImportError:
        pass
    except Exception:
        return ArtworkEntry(index, mime, None, None, False, "Artwork image could not be decoded.")
    return ArtworkEntry(index, mime, width, height, True)


def inspect_artwork(path: Path) -> ArtworkInfo:
    try:
        audio = File(path)
        pictures = list(getattr(audio, "pictures", None) or [])
        if not pictures:
            return ArtworkInfo(path, False, reason="No embedded artwork.")

        entries = tuple(_inspect_picture(index, picture) for index, picture in enumerate(pictures, start=1))
        first = entries[0]
        invalid = [entry for entry in entries if not entry.valid]
        reason = None
        if invalid:
            details = "; ".join(f"Artwork entry {entry.index}: {entry.reason}" for entry in invalid)
            reason = details
        return ArtworkInfo(
            path,
            True,
            first.mime,
            first.width,
            first.height,
            not invalid,
            reason,
            entries,
        )
    except Exception as exc:
        return ArtworkInfo(path, False, reason=f"Artwork inspection failed: {exc}")


def audit_artwork(tracks) -> list[ArtworkInfo]:
    return sorted((inspect_artwork(track.path) for track in tracks), key=lambda x: str(x.path))


def group_artwork_by_album(tracks, artwork=None):
    artwork = artwork or audit_artwork(tracks)
    by_path = {item.path: item for item in artwork}
    groups = defaultdict(list)
    for track in tracks:
        key = ((track.album or "<missing album>").casefold(), (getattr(track, "album_artist", None) or track.artist or "<missing artist>").casefold())
        groups[key].append(by_path[track.path])
    return dict(sorted(groups.items(), key=lambda item: item[0]))

from dataclasses import dataclass
from pathlib import Path
import re

from .scanner import Track


_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass(frozen=True)
class RenameSuggestion:
    source: Path
    destination: Path | None
    reason: str

    @property
    def has_change(self) -> bool:
        return self.destination is not None and self.destination != self.source


def sanitize_component(value: str, fallback: str = "Unknown") -> str:
    value = _INVALID_CHARS.sub("-", " ".join(value.split())).strip(" .")
    if not value:
        return fallback
    if value.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
        value = f"_{value}"
    return value[:180].rstrip(" .") or fallback


def suggested_filename(track: Track) -> str | None:
    if not track.title or not track.artist:
        return None
    artist = sanitize_component(track.artist)
    title = sanitize_component(track.title)
    prefix = f"{track.track_number:02d} - " if track.track_number is not None else ""
    return f"{prefix}{artist} - {title}{track.path.suffix.lower()}"


def suggest_renames(tracks: list[Track]) -> list[RenameSuggestion]:
    """Create collision-aware rename previews; never rename files."""
    suggestions: list[RenameSuggestion] = []
    planned: dict[Path, Path] = {}
    existing = {track.path.resolve() for track in tracks}

    for track in sorted(tracks, key=lambda item: str(item.path)):
        filename = suggested_filename(track)
        if filename is None:
            suggestions.append(RenameSuggestion(track.path, None, "Missing title or artist metadata."))
            continue

        destination = track.path.with_name(filename)
        if destination == track.path:
            suggestions.append(RenameSuggestion(track.path, destination, "Filename already matches metadata."))
            continue

        key = destination.resolve()
        if key in existing and key != track.path.resolve():
            suggestions.append(RenameSuggestion(track.path, None, f"Collision with existing file: {destination.name}"))
            continue
        if key in planned.values():
            suggestions.append(RenameSuggestion(track.path, None, f"Collision with another planned rename: {destination.name}"))
            continue

        planned[track.path] = key
        suggestions.append(RenameSuggestion(track.path, destination, "Metadata-based filename suggestion."))

    return suggestions

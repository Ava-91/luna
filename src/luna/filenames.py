from dataclasses import dataclass
from pathlib import Path
import re

from .scanner import Track


_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
# Windows-invalid punctuation that should be replaced with a separator. Quotes are
# treated separately: they are cosmetic and should not create extra separators.
_INVALID_CHARS = re.compile(r'[<>:/\\|?*\x00-\x1f]')
_QUOTES = re.compile(r'[\"]')


@dataclass(frozen=True)
class RenameSuggestion:
    source: Path
    destination: Path | None
    reason: str

    @property
    def has_change(self) -> bool:
        return self.destination is not None and self.destination != self.source


def sanitize_component(value: str, fallback: str = "Unknown") -> str:
    value = " ".join(value.split())
    value = _INVALID_CHARS.sub("-", value)
    value = _QUOTES.sub("", value)
    value = value.strip(" .")
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
    planned: set[Path] = set()
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
        # Check both the scanned set and the filesystem. This keeps the planner
        # safe when callers provide only a subset of the directory contents.
        if (key in existing and key != track.path.resolve()) or destination.exists():
            suggestions.append(RenameSuggestion(track.path, None, f"Collision with existing file: {destination.name}"))
            continue
        if key in planned:
            suggestions.append(RenameSuggestion(track.path, None, f"Collision with another planned rename: {destination.name}"))
            continue

        planned.add(key)
        suggestions.append(RenameSuggestion(track.path, destination, "Metadata-based filename suggestion."))

    return suggestions

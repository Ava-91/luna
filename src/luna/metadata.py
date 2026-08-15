from dataclasses import dataclass
from pathlib import Path

from .scanner import Track


PLACEHOLDER_VALUES = {
    "unknown",
    "unknown artist",
    "unknown album",
    "untitled",
    "track",
    "track 1",
    "n/a",
    "na",
}


@dataclass(frozen=True)
class MetadataIssue:
    field: str
    message: str


@dataclass(frozen=True)
class TrackValidation:
    path: Path
    issues: tuple[MetadataIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def validate_track(track: Track) -> TrackValidation:
    issues: list[MetadataIssue] = []
    values = {
        "title": track.title,
        "artist": track.artist,
        "album": track.album,
    }

    for field, value in values.items():
        if value is None or not value.strip():
            issues.append(MetadataIssue(field, f"Missing {field} metadata."))
        elif value.strip().casefold() in PLACEHOLDER_VALUES:
            issues.append(MetadataIssue(field, f"Placeholder {field} metadata: {value!r}."))

    return TrackValidation(track.path, tuple(issues))


def validate_library(tracks: list[Track]) -> list[TrackValidation]:
    """Validate metadata without changing any files."""
    return [validate_track(track) for track in tracks]

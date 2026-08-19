from dataclasses import dataclass
from pathlib import Path
from .scanner import Track

PLACEHOLDER_VALUES = {"unknown", "unknown artist", "unknown album", "untitled", "track", "track 1", "n/a", "na"}

@dataclass(frozen=True)
class MetadataIssue:
    field: str
    message: str

@dataclass(frozen=True)
class TrackValidation:
    path: Path
    issues: tuple[MetadataIssue, ...]
    @property
    def valid(self):
        return not self.issues

def validate_track(track: Track):
    issues = []
    # Core metadata is deliberately limited to the fields users expect from a
    # basic Track object. Optional fields are validated only when supplied.
    for field in ("title", "artist", "album"):
        value = getattr(track, field, None)
        if value is None or not value.strip():
            issues.append(MetadataIssue(field, f"Missing {field} metadata."))
        elif value.strip().casefold() in PLACEHOLDER_VALUES:
            issues.append(MetadataIssue(field, f"Placeholder {field} metadata: {value!r}."))
    if track.track_number is not None and track.track_number < 1:
        issues.append(MetadataIssue("track_number", "Track number must be positive."))
    if track.disc_number is not None and track.disc_number < 1:
        issues.append(MetadataIssue("disc_number", "Disc number must be positive."))
    if track.year is not None and not 1000 <= track.year <= 3000:
        issues.append(MetadataIssue("year", f"Suspicious year: {track.year}."))
    # Parser errors are real validation failures, but only when the scanner
    # actually encountered one; ordinary hand-built Track objects remain valid.
    if track.metadata_error:
        issues.append(MetadataIssue("parser", track.metadata_error))
    return TrackValidation(track.path, tuple(issues))

def validate_library(tracks):
    return [validate_track(track) for track in tracks]

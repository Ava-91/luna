from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .scanner import Track


@dataclass(frozen=True)
class DuplicateGroup:
    digest: str
    tracks: tuple[Track, ...]

    @property
    def size(self):
        return len(self.tracks)


@dataclass(frozen=True)
class ProbableDuplicate:
    tracks: tuple[Track, ...]
    confidence: float
    reasons: tuple[str, ...]


def hash_file(path: Path, chunk_size=1024 * 1024):
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(tracks):
    by_size = defaultdict(list)
    for track in tracks:
        try:
            by_size[track.path.stat().st_size].append(track)
        except OSError:
            continue

    by_hash = defaultdict(list)
    for items in by_size.values():
        if len(items) < 2:
            continue
        for track in items:
            try:
                by_hash[hash_file(track.path)].append(track)
            except OSError:
                continue

    return sorted(
        (
            DuplicateGroup(digest, tuple(sorted(items, key=lambda x: str(x.path))))
            for digest, items in by_hash.items()
            if len(items) > 1
        ),
        key=lambda x: x.digest,
    )


def _normalized(value):
    return (value or "").strip().casefold()


def probable_duplicate_score(first: Track, second: Track) -> tuple[float, tuple[str, ...]]:
    """Return an explainable probability-like score from independent metadata signals."""
    score = 0.0
    reasons = []

    if _normalized(first.artist) and _normalized(first.artist) == _normalized(second.artist):
        score += 0.30
        reasons.append("artist matches")
    if _normalized(first.title) and _normalized(first.title) == _normalized(second.title):
        score += 0.30
        reasons.append("title matches")
    if _normalized(first.album) and _normalized(first.album) == _normalized(second.album):
        score += 0.15
        reasons.append("album matches")
    if first.track_number is not None and first.track_number == second.track_number:
        score += 0.10
        reasons.append("track number matches")
    if first.disc_number is not None and first.disc_number == second.disc_number:
        score += 0.05
        reasons.append("disc number matches")
    if first.size is not None and second.size is not None and first.size == second.size:
        score += 0.10
        reasons.append("file size matches")
    if first.year is not None and second.year is not None and first.year == second.year:
        score += 0.05
        reasons.append("year matches")

    return round(min(score, 0.99), 2), tuple(reasons)


def _group_reasons(reason_sets):
    common = set(reason_sets[0])
    for reasons in reason_sets[1:]:
        common.intersection_update(reasons)
    return tuple(reason for reason in reason_sets[0] if reason in common)


def find_probable_duplicates(tracks):
    buckets = defaultdict(list)
    for track in tracks:
        artist = _normalized(track.artist)
        title = _normalized(track.title)
        if artist and title:
            buckets[(artist, title)].append(track)

    results = []
    for items in buckets.values():
        remaining = list(sorted(items, key=lambda x: str(x.path)))
        while len(remaining) >= 2:
            representative = remaining.pop(0)
            matches = []
            match_scores = []
            match_reasons = []
            for candidate in remaining:
                score, reasons = probable_duplicate_score(representative, candidate)
                if score >= 0.60:
                    matches.append(candidate)
                    match_scores.append(score)
                    match_reasons.append(reasons)

            if matches:
                group = (representative, *matches)
                confidence = min(match_scores)
                reasons = _group_reasons(match_reasons)
                if len({track.path.suffix.lower() for track in group}) > 1:
                    reasons = reasons + ("different file formats",)
                results.append(ProbableDuplicate(tuple(group), confidence, reasons))
                matched = set(matches)
                remaining = [track for track in remaining if track not in matched]

    return sorted(results, key=lambda x: tuple(str(t.path) for t in x.tracks))

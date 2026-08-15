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
    def size(self) -> int:
        return len(self.tracks)


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a SHA-256 digest using bounded memory."""
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(tracks: list[Track]) -> list[DuplicateGroup]:
    """Group byte-identical files without modifying them."""
    by_hash: dict[str, list[Track]] = defaultdict(list)
    for track in tracks:
        by_hash[hash_file(track.path)].append(track)

    groups = [
        DuplicateGroup(digest, tuple(sorted(items, key=lambda track: str(track.path))))
        for digest, items in by_hash.items()
        if len(items) > 1
    ]
    return sorted(groups, key=lambda group: group.digest)

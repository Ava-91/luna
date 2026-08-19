from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class MetadataCandidate:
    field: str
    value: str
    source: str
    confidence: float

class MetadataProvider(Protocol):
    name: str
    def candidates(self, artist: str|None, title: str|None, album: str|None) -> list[MetadataCandidate]: ...

class LocalOnlyProvider:
    name="local"
    def candidates(self, artist, title, album): return []

def rank_candidates(candidates):
    return sorted(candidates,key=lambda c:(-c.confidence,c.source,c.field,c.value.casefold()))

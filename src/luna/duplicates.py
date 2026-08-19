from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from .scanner import Track

@dataclass(frozen=True)
class DuplicateGroup:
    digest:str
    tracks:tuple[Track,...]
    @property
    def size(self):return len(self.tracks)

@dataclass(frozen=True)
class ProbableDuplicate:
    tracks:tuple[Track,...]
    confidence:float
    reasons:tuple[str,...]

def hash_file(path:Path,chunk_size=1024*1024):
    digest=sha256()
    with path.open("rb") as handle:
        while chunk:=handle.read(chunk_size):digest.update(chunk)
    return digest.hexdigest()

def find_duplicates(tracks):
    by_hash=defaultdict(list)
    for track in tracks:
        try: by_hash[hash_file(track.path)].append(track)
        except OSError: continue
    return sorted((DuplicateGroup(d,tuple(sorted(items,key=lambda x:str(x.path)))) for d,items in by_hash.items() if len(items)>1),key=lambda x:x.digest)

def find_probable_duplicates(tracks):
    groups=defaultdict(list)
    for track in tracks:
        key=((track.artist or "").strip().casefold(),(track.title or "").strip().casefold(),track.size)
        if key[0] and key[1]:groups[key].append(track)
    results=[]
    for items in groups.values():
        if len(items)>1:
            reasons=["artist and title match","file size matches"]
            if len({track.path.suffix.lower() for track in items})>1: reasons=["artist and title match"]
            results.append(ProbableDuplicate(tuple(sorted(items,key=lambda x:str(x.path))),0.95 if len(reasons)==2 else 0.85,tuple(reasons)))
    return sorted(results,key=lambda x:tuple(str(t.path) for t in x.tracks))

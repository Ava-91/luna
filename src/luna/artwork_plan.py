from dataclasses import dataclass
from pathlib import Path
from .artwork import group_artwork_by_album

@dataclass(frozen=True)
class ArtworkCandidate:
    album:str
    album_artist:str
    source:Path
    confidence:float
    reason:str
@dataclass(frozen=True)
class ArtworkChange:
    album:str
    album_artist:str
    tracks:tuple[Path,...]
    current:str
    candidate:ArtworkCandidate|None

def rank_candidates(candidates):
    return sorted(candidates,key=lambda c:(-c.confidence,c.source.suffix.casefold(),str(c.source).casefold()))

def build_artwork_plan(tracks,candidates=None):
    candidates=rank_candidates(candidates or []); by_album=group_artwork_by_album(tracks); candidate_map={}
    for candidate in candidates: candidate_map.setdefault((candidate.album.casefold(),candidate.album_artist.casefold()),candidate)
    result=[]
    for (album,artist),items in by_album.items():
        paths=tuple(sorted((x.path for x in items),key=str)); missing=any(not x.has_artwork or not x.valid for x in items)
        if missing: result.append(ArtworkChange(album,artist,paths,"missing_or_invalid",candidate_map.get((album,artist))))
    return result

def local_candidates(directory:Path,album:str,album_artist:str):
    names={"cover","folder","front","albumart","album-art"}; result=[]
    for path in sorted(directory.iterdir() if directory.exists() else [],key=lambda p:p.name.casefold()):
        if path.is_file() and path.suffix.lower() in {".jpg",".jpeg",".png",".webp"} and path.stem.casefold() in names: result.append(ArtworkCandidate(album,album_artist,path,0.9,"recognized local cover filename"))
    return rank_candidates(result)

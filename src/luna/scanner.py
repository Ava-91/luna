from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from mutagen import File

AUDIO_EXTENSIONS={".mp3",".flac",".m4a",".aac",".ogg",".opus",".wav",".wma"}

@dataclass(frozen=True)
class Track:
    path: Path
    title: str|None
    artist: str|None
    album: str|None
    track_number: int|None=None
    album_artist: str|None=None
    disc_number: int|None=None
    year: int|None=None
    genre: str|None=None
    format: str|None=None
    size: int=0
    modified: float=0.0
    raw_metadata: dict[str,object]|None=None
    metadata_error: str|None=None

def _first(tags,key):
    if tags is None or not hasattr(tags,"get"): return None
    value=tags.get(key)
    if isinstance(value,(list,tuple)): return str(value[0]) if value else None
    return str(value) if value is not None else None

def _number(value):
    try:return int(str(value).split("/",1)[0]) if value else None
    except (ValueError,TypeError):return None

def _year(value):
    if not value:return None
    try:return int(str(value)[:4])
    except ValueError:return None

def inspect_file(path:Path)->Track:
    try: stat=path.stat()
    except OSError as exc: return Track(path,None,None,None,format=path.suffix.lower().lstrip("."),metadata_error=str(exc))
    try:
        audio=File(path,easy=True)
        if audio is None: return Track(path,None,None,None,format=path.suffix.lower().lstrip("."),size=stat.st_size,modified=stat.st_mtime,raw_metadata={},metadata_error="Audio file could not be parsed.")
        tags=audio.tags; raw={str(k):v for k,v in (tags.items() if hasattr(tags,"items") else [])}
        return Track(path,_first(tags,"title"),_first(tags,"artist"),_first(tags,"album"),_number(_first(tags,"tracknumber")),_first(tags,"albumartist"),_number(_first(tags,"discnumber")),_year(_first(tags,"date") or _first(tags,"year")),_first(tags,"genre"),path.suffix.lower().lstrip("."),stat.st_size,stat.st_mtime,raw)
    except Exception as exc:
        return Track(path,None,None,None,format=path.suffix.lower().lstrip("."),size=stat.st_size,modified=stat.st_mtime,raw_metadata={},metadata_error=str(exc))

def scan_library(root:Path,extensions=None,ignored_paths=None,workers=4,on_error=None)->list[Track]:
    extensions={x.lower() if x.startswith(".") else "."+x.lower() for x in (extensions or AUDIO_EXTENSIONS)}; ignored={Path(x).resolve() for x in (ignored_paths or [])}; paths=[]
    for path in sorted(root.rglob("*")):
        try:
            resolved=path.resolve()
            if path.is_file() and path.suffix.lower() in extensions and not any(parent in ignored for parent in (resolved,*resolved.parents)): paths.append(path)
        except OSError as exc:
            if on_error:on_error(path,exc)
    with ThreadPoolExecutor(max_workers=max(1,workers)) as pool: tracks=list(pool.map(inspect_file,paths))
    return sorted(tracks,key=lambda x:str(x.path))

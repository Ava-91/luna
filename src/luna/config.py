from dataclasses import dataclass, asdict
from pathlib import Path
import json

DEFAULT_EXTENSIONS=(".mp3",".flac",".m4a",".aac",".ogg",".opus",".wav",".wma")
@dataclass
class LibraryProfile:
    roots: list[str]
    extensions: list[str]
    ignored_paths: list[str]
    max_workers: int = 4
    filename_template: str = "{track} - {artist} - {title}"

    @classmethod
    def defaults(cls): return cls([], list(DEFAULT_EXTENSIONS), [])

def config_path() -> Path:
    return Path.home()/".config"/"luna"/"config.json"

def load_config(path: Path|None=None) -> LibraryProfile:
    path=path or config_path()
    if not path.exists(): return LibraryProfile.defaults()
    data=json.loads(path.read_text(encoding="utf-8")); defaults=asdict(LibraryProfile.defaults()); defaults.update(data)
    return LibraryProfile(**defaults)

def save_config(profile: LibraryProfile, path: Path|None=None):
    path=path or config_path(); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(asdict(profile),indent=2),encoding="utf-8")

def reset_config(path: Path|None=None):
    path=path or config_path()
    if path.exists(): path.unlink()

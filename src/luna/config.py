from dataclasses import dataclass, asdict
from pathlib import Path
from string import Formatter
import json

DEFAULT_EXTENSIONS = (".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".wma")
_CONFIG_FIELDS = {"roots", "extensions", "ignored_paths", "max_workers", "filename_template"}
_SUPPORTED_FILENAME_FIELDS = {"track", "artist", "title", "album", "album_artist", "disc", "year", "genre", "format"}


@dataclass
class LibraryProfile:
    roots: list[str]
    extensions: list[str]
    ignored_paths: list[str]
    max_workers: int = 4
    filename_template: str = "{track} - {artist} - {title}"

    @classmethod
    def defaults(cls):
        return cls([], list(DEFAULT_EXTENSIONS), [])


def _validate_filename_template(template: str) -> None:
    formatter = Formatter()
    try:
        parts = list(formatter.parse(template))
    except ValueError as exc:
        raise ValueError(f"Configuration 'filename_template' is invalid: {exc}") from exc

    for _, field_name, format_spec, _ in parts:
        if field_name is not None and field_name not in _SUPPORTED_FILENAME_FIELDS:
            raise ValueError(f"Configuration 'filename_template' uses unsupported field: {field_name}")
        if format_spec:
            _validate_filename_template(format_spec)


def validate_profile(profile: LibraryProfile) -> LibraryProfile:
    if not isinstance(profile.roots, list) or not all(isinstance(value, str) and value.strip() for value in profile.roots):
        raise ValueError("Configuration 'roots' must be a list of non-empty strings.")
    if not isinstance(profile.extensions, list) or not profile.extensions or not all(isinstance(value, str) and value.strip() for value in profile.extensions):
        raise ValueError("Configuration 'extensions' must be a non-empty list of strings.")
    if not isinstance(profile.ignored_paths, list) or not all(isinstance(value, str) and value.strip() for value in profile.ignored_paths):
        raise ValueError("Configuration 'ignored_paths' must be a list of non-empty strings.")
    if isinstance(profile.max_workers, bool) or not isinstance(profile.max_workers, int) or profile.max_workers < 1:
        raise ValueError("Configuration 'max_workers' must be a positive integer.")
    if not isinstance(profile.filename_template, str) or not profile.filename_template.strip():
        raise ValueError("Configuration 'filename_template' must be a non-empty string.")
    _validate_filename_template(profile.filename_template)
    return profile


def _profile_from_data(data) -> LibraryProfile:
    if not isinstance(data, dict):
        raise ValueError("Configuration file must contain a JSON object.")
    unknown = sorted(set(data) - _CONFIG_FIELDS)
    if unknown:
        raise ValueError(f"Unknown configuration field(s): {', '.join(unknown)}")
    defaults = asdict(LibraryProfile.defaults())
    defaults.update(data)
    return validate_profile(LibraryProfile(**defaults))


def config_path() -> Path:
    return Path.home() / ".config" / "luna" / "config.json"


def load_config(path: Path | None = None) -> LibraryProfile:
    path = path or config_path()
    if not path.exists():
        return LibraryProfile.defaults()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in configuration file: {exc.msg}") from exc
    return _profile_from_data(data)


def save_config(profile: LibraryProfile, path: Path | None = None):
    validate_profile(profile)
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(profile), indent=2), encoding="utf-8")


def reset_config(path: Path | None = None):
    path = path or config_path()
    if path.exists():
        path.unlink()

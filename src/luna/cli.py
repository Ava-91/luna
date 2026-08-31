import argparse, json, time
from pathlib import Path

from mutagen import File

from .scanner import scan_library
from .metadata import validate_library
from .duplicates import find_duplicates, find_probable_duplicates
from .planner import build_rename_plan
from .artwork import audit_artwork
from .artwork_plan import build_artwork_plan, local_candidates
from .normalize import normalization_plan
from .report import build_report, render_report
from .config import load_config, save_config, reset_config
from .export import export_json, export_text, export_markdown
from .apply import apply_rename_plan
from .metadata_apply import build_metadata_plan, apply_metadata_plan
from .backup import OperationLog, rollback


def load_tracks(path):
    profile = load_config()
    return scan_library(path, profile.extensions, profile.ignored_paths, profile.max_workers)


def _benchmark(path):
    timings = {}
    start = time.perf_counter()
    tracks = load_tracks(path)
    timings["scan"] = time.perf_counter() - start
    for name, operation in (
        ("metadata_validation", lambda: validate_library(tracks)),
        ("exact_duplicates", lambda: find_duplicates(tracks)),
        ("probable_duplicates", lambda: find_probable_duplicates(tracks)),
        ("artwork_audit", lambda: audit_artwork(tracks)),
        ("rename_plan", lambda: build_rename_plan(tracks)),
        ("normalization_plan", lambda: normalization_plan(tracks)),
    ):
        start = time.perf_counter()
        operation()
        timings[name] = time.perf_counter() - start
    timings["total"] = sum(timings.values())
    return {"tracks": len(tracks), "seconds": timings}


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _embed_artwork(path: Path, image_path: Path) -> None:
    """Replace embedded artwork using a local image, without touching the source image."""
    if not image_path.is_file():
        raise FileNotFoundError(f"Artwork file does not exist: {image_path}")

    suffix = image_path.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(suffix)
    if mime is None:
        raise ValueError("Artwork must be a JPG, JPEG, PNG, or WEBP image.")
    data = image_path.read_bytes()
    audio = File(path)
    if audio is None:
        raise OSError("Audio file could not be parsed.")

    if hasattr(audio, "clear_pictures") and hasattr(audio, "add_picture"):
        from mutagen.flac import Picture

        audio.clear_pictures()
        picture = Picture()
        picture.type = 3
        picture.mime = mime
        picture.desc = "Cover"
        picture.data = data
        audio.add_picture(picture)
        audio.save()
        return

    if path.suffix.lower() in {".m4a", ".mp4"}:
        from mutagen.mp4 import MP4Cover

        if audio.tags is None:
            audio.add_tags()
        image_format = MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG
        audio.tags["covr"] = [MP4Cover(data, imageformat=image_format)]
        audio.save()
        return

    if path.suffix.lower() != ".mp3":
        raise ValueError("Embedded artwork replacement is currently supported for MP3, FLAC, and M4A files.")
    from mutagen.id3 import APIC, ID3

    tags = ID3(path)
    tags.delall("APIC")
    tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
    tags.save(path)


def apply_artwork_changes(root: Path, tracks, confirm: bool, log_path: Path | None):
    if not confirm:
        raise PermissionError("Applying artwork changes requires explicit confirmation (confirm=True).")

    candidates = []
    for track in tracks:
        if _inside(root, track.path.parent):
            album = track.album or "<missing album>"
            artist = getattr(track, "album_artist", None) or track.artist or "<missing artist>"
            candidates.extend(local_candidates(track.path.parent, album, artist))

    plan = build_artwork_plan(tracks, candidates)
    log = OperationLog(log_path) if log_path else None
    results = []
    for change in plan:
        candidate = change.candidate
        if candidate is None:
            for path in change.tracks:
                results.append({"path": str(path), "success": False, "error": "No local cover candidate found."})
            continue
        if not _inside(root, candidate.source):
            for path in change.tracks:
                results.append({"path": str(path), "success": False, "error": "Artwork candidate is outside the selected library."})
            continue
        for path in change.tracks:
            try:
                _embed_artwork(path, candidate.source)
                if log:
                    log.record("artwork", path, candidate.source)
                results.append({"path": str(path), "source": str(candidate.source), "success": True, "error": None})
            except Exception as exc:
                results.append({"path": str(path), "source": str(candidate.source), "success": False, "error": str(exc)})
    if log:
        log.save()
    return results


def _build_report_payload(tracks):
    """Build the shared report data used by report and export commands."""
    validations = validate_library(tracks)
    duplicates = find_duplicates(tracks)
    art = audit_artwork(tracks)
    renames = build_rename_plan(tracks)
    return build_report(tracks, validations, duplicates, art, renames)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Luna — local-first music library cleaner")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("scan", help="Read-only scan")
    p.add_argument("path", type=Path)
    p.add_argument("--json", action="store_true")
    for name, help_text in (("inspect", "Validate metadata"), ("duplicates", "Find exact and probable duplicates"), ("artwork", "Audit embedded artwork"), ("artwork-plan", "Preview artwork replacement candidates"), ("normalize-plan", "Preview metadata normalization"), ("rename-plan", "Preview safe filename changes"), ("report", "Build library health report")):
        q = sub.add_parser(name, help=help_text)
        q.add_argument("path", type=Path)
        q.add_argument("--output", type=Path)
        q.add_argument("--format", choices=("text", "json", "markdown"), default="text")

    q = sub.add_parser("benchmark", help="Measure read-only library analysis timings")
    q.add_argument("path", type=Path)
    q.add_argument("--json", action="store_true")

    q = sub.add_parser("apply", help="Apply a reviewed plan; explicit --confirm required")
    q.add_argument("path", type=Path)
    q.add_argument("--confirm", action="store_true")
    q.add_argument("--metadata", action="store_true", help="Apply reviewed metadata normalization instead of renames")
    q.add_argument("--artwork", action="store_true", help="Embed local cover candidates into affected tracks")
    q.add_argument("--log", type=Path, default=Path(".luna-operations.json"))

    q = sub.add_parser("rollback", help="Rollback an operation log")
    q.add_argument("log", type=Path)
    q.add_argument("--confirm", action="store_true")
    q = sub.add_parser("config", help="Manage library profile")
    q.add_argument("action", choices=("show", "set", "reset"))
    q.add_argument("roots", nargs="*")
    sub.add_parser("gui", help="Launch optional PySide6 interface")
    q = sub.add_parser("export", help="Export a read-only scan report")
    q.add_argument("path", type=Path)
    q.add_argument("output", type=Path)

    args = parser.parse_args(argv)
    if args.command == "config":
        if args.action == "show":
            print(json.dumps(load_config().__dict__, indent=2))
            return
        if args.action == "reset":
            reset_config()
            return
        profile = load_config()
        profile.roots = args.roots
        save_config(profile)
        print("Configuration saved.")
        return
    if args.command == "rollback":
        if not args.confirm:
            parser.error("rollback requires --confirm")
        print(json.dumps(rollback(args.log, True), indent=2))
        return
    if args.command == "gui":
        from .gui import launch
        raise SystemExit(launch())

    root = args.path.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"Not a directory: {root}")

    if args.command == "benchmark":
        payload = _benchmark(root)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        print(f"Scanned {payload['tracks']} audio file(s).")
        for name, seconds in payload["seconds"].items():
            print(f"{name}: {seconds:.6f}s")
        return

    tracks = load_tracks(root)

    if args.command in {"scan", "inspect"}:
        validations = validate_library(tracks)
        payload = [{"path": str(t.path), "title": t.title, "artist": t.artist, "album": t.album, "format": t.format, "metadata_error": t.metadata_error, "issues": [i.message for i in v.issues]} for t, v in zip(tracks, validations)]
        if getattr(args, "json", False):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        for row in payload:
            print(f"{row['artist'] or '<missing artist>'} — {row['title'] or '<missing title>'} [{row['album'] or '<missing album>'}] :: {row['path']}")
            for issue in row["issues"]:
                print(f"  ! {issue}")
        print(f"Found {len(tracks)} audio file(s). Metadata issues: {sum(not v.valid for v in validations)}.")
        return

    if args.command == "duplicates":
        duplicates = find_duplicates(tracks)
        probable = find_probable_duplicates(tracks)
        payload = {"exact": [{"digest": g.digest, "files": [str(t.path) for t in g.tracks]} for g in duplicates], "probable": [{"confidence": g.confidence, "reasons": list(g.reasons), "files": [str(t.path) for t in g.tracks]} for g in probable]}
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.command == "artwork":
        art = audit_artwork(tracks)
        text = json.dumps([x.__dict__ | {"path": str(x.path)} for x in art], default=str, ensure_ascii=False, indent=2)
    elif args.command == "artwork-plan":
        text = json.dumps([{"album": x.album, "album_artist": x.album_artist, "tracks": [str(p) for p in x.tracks], "current": x.current, "candidate": str(x.candidate.source) if x.candidate else None} for x in build_artwork_plan(tracks)], ensure_ascii=False, indent=2)
    elif args.command == "normalize-plan":
        text = json.dumps([x.__dict__ for x in normalization_plan(tracks)], default=str, ensure_ascii=False, indent=2)
    elif args.command == "rename-plan":
        renames = build_rename_plan(tracks)
        text = json.dumps([{"source": str(x.source), "destination": str(x.destination) if x.destination else None, "status": x.status, "reason": x.reason} for x in renames], ensure_ascii=False, indent=2)
    elif args.command == "report":
        payload = _build_report_payload(tracks)
        text = render_report(payload) if args.format == "text" else json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.command == "export":
        payload = _build_report_payload(tracks)
        export_json(payload, args.output)
        print(f"Wrote {args.output}")
        return
    elif args.command == "apply":
        selected = sum((args.metadata, args.artwork))
        if selected > 1:
            parser.error("Choose only one of --metadata or --artwork")
        if not args.confirm:
            parser.error("apply requires --confirm")
        if args.artwork:
            print(json.dumps(apply_artwork_changes(root, tracks, True, args.log), ensure_ascii=False, indent=2))
            return
        if args.metadata:
            results = apply_metadata_plan(build_metadata_plan(tracks), True, args.log)
            print(json.dumps([{"path": str(item.path), "field": item.field, "success": ok, "error": error} for item, ok, error in results], indent=2))
            return
        renames = build_rename_plan(tracks)
        results = apply_rename_plan(renames, True, args.log)
        print(json.dumps([{"source": str(r.source), "destination": str(r.destination), "success": r.success, "error": r.error} for r in results], indent=2))
        return
    else:
        return

    if args.output:
        if args.format == "markdown":
            export_markdown("Luna report", {"Summary": text}, args.output)
        else:
            export_text(text, args.output)
    else:
        print(text)


if __name__ == "__main__":
    main()

import argparse
from pathlib import Path

from .duplicates import find_duplicates
from .filenames import suggest_renames
from .metadata import validate_library
from .scanner import scan_library


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and clean a local music library.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Scan a music folder (read-only).")
    scan.add_argument("path", type=Path)

    args = parser.parse_args()

    if args.command == "scan":
        root = args.path.expanduser().resolve()
        if not root.is_dir():
            parser.error(f"Not a directory: {root}")

        tracks = scan_library(root)
        validations = validate_library(tracks)
        duplicate_groups = find_duplicates(tracks)
        rename_suggestions = suggest_renames(tracks)
        problematic = [result for result in validations if not result.valid]
        proposed = [item for item in rename_suggestions if item.has_change]

        print(f"Found {len(tracks)} audio file(s).")
        print(f"Metadata issues: {len(problematic)} file(s).")
        print(f"Duplicate groups: {len(duplicate_groups)}.")
        print(f"Filename suggestions: {len(proposed)}.")

        for track, validation in zip(tracks, validations):
            title = track.title or "<missing title>"
            artist = track.artist or "<missing artist>"
            album = track.album or "<missing album>"
            print(f"- {artist} — {title} [{album}] :: {track.path}")
            for issue in validation.issues:
                print(f"  ! {issue.message}")

        for suggestion in rename_suggestions:
            if suggestion.has_change:
                print(f"  → {suggestion.source.name} -> {suggestion.destination.name}")
            elif suggestion.destination is None:
                print(f"  ! {suggestion.source.name}: {suggestion.reason}")

        for index, group in enumerate(duplicate_groups, start=1):
            print(f"Duplicate group {index} ({group.size} files, {group.digest[:12]}…):")
            for track in group.tracks:
                print(f"  = {track.path}")


if __name__ == "__main__":
    main()

import argparse
from pathlib import Path

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
        problematic = [result for result in validations if not result.valid]

        print(f"Found {len(tracks)} audio file(s).")
        print(f"Metadata issues: {len(problematic)} file(s).")

        for track, validation in zip(tracks, validations):
            title = track.title or "<missing title>"
            artist = track.artist or "<missing artist>"
            album = track.album or "<missing album>"
            print(f"- {artist} — {title} [{album}] :: {track.path}")
            for issue in validation.issues:
                print(f"  ! {issue.message}")


if __name__ == "__main__":
    main()

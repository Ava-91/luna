import argparse
from pathlib import Path

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
        print(f"Found {len(tracks)} audio file(s).")
        for track in tracks:
            title = track.title or "<missing title>"
            artist = track.artist or "<missing artist>"
            album = track.album or "<missing album>"
            print(f"- {artist} — {title} [{album}] :: {track.path}")


if __name__ == "__main__":
    main()

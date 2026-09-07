import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from luna.config import LibraryProfile
from luna.filenames import sanitize_component, suggest_renames, suggested_filename
from luna.planner import build_rename_plan
from luna.scanner import Track


class FilenameSuggestionTests(unittest.TestCase):
    def test_builds_artist_title_filename_with_track_number(self) -> None:
        track = Track(Path("old.MP3"), "Bad Guy", "Billie Eilish", "Album", 3)
        self.assertEqual(suggested_filename(track), "03 - Billie Eilish - Bad Guy.mp3")

    def test_default_template_without_track_number_preserves_existing_behavior(self) -> None:
        track = Track(Path("old.mp3"), "Song", "Artist", "Album")
        self.assertEqual(suggested_filename(track), "Artist - Song.mp3")

    def test_custom_template_uses_relevant_metadata(self) -> None:
        track = Track(Path("old.mp3"), "Song", "Artist", "Album", 3, "Album Artist", 2, 2024, "Rock", "mp3")
        self.assertEqual(
            suggested_filename(track, "{artist} - {album} - {track} - {title} ({year})"),
            "Artist - Album - 03 - Song (2024).mp3",
        )

    def test_configured_template_flows_through_rename_planner(self) -> None:
        track = Track(Path("old.mp3"), "Song", "Artist", "Album", 3)
        profile = LibraryProfile([], [".mp3"], [], filename_template="{album}/{title}")
        with patch("luna.planner.load_config", return_value=profile):
            plan = build_rename_plan([track])
        self.assertEqual(plan[0].destination, Path("Album-Song.mp3"))

    def test_invalid_template_is_reported(self) -> None:
        track = Track(Path("old.mp3"), "Song", "Artist", "Album")
        with self.assertRaisesRegex(ValueError, "Invalid filename template"):
            suggested_filename(track, "{missing} - {title}")

    def test_sanitizes_unsafe_characters_and_reserved_names(self) -> None:
        self.assertEqual(sanitize_component('AC/DC: "Live"'), "AC-DC- Live")
        self.assertEqual(sanitize_component("CON"), "_CON")

    def test_missing_metadata_has_no_automatic_name(self) -> None:
        track = Track(Path("track.mp3"), None, "Artist", None)
        self.assertIsNone(suggested_filename(track))

    def test_existing_collision_is_not_suggested_as_safe_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "bad.mp3"
            collision = root / "Artist - Song.mp3"
            first.write_bytes(b"audio")
            collision.write_bytes(b"other audio")
            track = Track(first, "Song", "Artist", "Album")

            result = suggest_renames([track])
            self.assertFalse(result[0].has_change)
            self.assertIn("Collision", result[0].reason)

    def test_suggestions_do_not_modify_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.mp3"
            path.write_bytes(b"audio")
            track = Track(path, "Song", "Artist", "Album")
            suggest_renames([track])
            self.assertTrue(path.exists())
            self.assertEqual(path.read_bytes(), b"audio")


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from luna.metadata import validate_library, validate_track
from luna.metadata_apply import MetadataChange, apply_metadata_plan
from luna.scanner import Track


class MetadataValidationTests(unittest.TestCase):
    def test_complete_metadata_is_valid(self) -> None:
        track = Track(Path("song.mp3"), "Song", "Artist", "Album")
        result = validate_track(track)
        self.assertTrue(result.valid)
        self.assertEqual(result.issues, ())

    def test_missing_metadata_is_reported(self) -> None:
        track = Track(Path("song.mp3"), None, "Artist", "")
        result = validate_track(track)
        self.assertEqual({issue.field for issue in result.issues}, {"title", "album"})

    def test_placeholder_metadata_is_reported(self) -> None:
        track = Track(Path("song.mp3"), "Untitled", "Unknown Artist", "Album")
        result = validate_track(track)
        self.assertEqual({issue.field for issue in result.issues}, {"title", "artist"})

    def test_validation_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "song.mp3"
            path.write_bytes(b"not an audio file")
            track = Track(path, None, None, None)
            validate_library([track])
            self.assertEqual(path.read_bytes(), b"not an audio file")

    def test_metadata_apply_uses_easy_field_names(self) -> None:
        path = Path("song.mp3")
        audio = Mock()
        audio.tags = Mock()
        with patch("luna.metadata_apply.File", return_value=audio) as open_file:
            result = apply_metadata_plan(
                [MetadataChange(path, "title", " Old Title ", "New Title")],
                confirm=True,
            )

        self.assertTrue(result[0][1])
        open_file.assert_called_once_with(path, easy=True)
        self.assertEqual(audio.__getitem__.call_args, None)
        audio.__setitem__.assert_called_once_with("title", ["New Title"])
        audio.save.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

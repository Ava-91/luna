import tempfile
import unittest
from pathlib import Path

from luna.metadata import validate_library, validate_track
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


if __name__ == "__main__":
    unittest.main()

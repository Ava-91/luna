import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from luna.scanner import Track, scan_library


class _DisappearingIndex:
    def unchanged(self, path):
        return False

    def get_track(self, path):
        return None

    def upsert(self, track):
        track.path.unlink()
        raise FileNotFoundError(track.path)

    def close(self):
        return None


class ScannerIndexRaceTests(unittest.TestCase):
    def test_file_disappearing_before_index_upsert_does_not_abort_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            errors = []
            track = Track(path, "Song", "Artist", "Album", format="mp3", size=5, modified=path.stat().st_mtime)

            with patch("luna.scanner.inspect_file", return_value=track):
                result = scan_library(root, extensions=[".mp3"], index=_DisappearingIndex(), on_error=errors.append)

            self.assertEqual(result, [track])
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], FileNotFoundError)


if __name__ == "__main__":
    unittest.main()

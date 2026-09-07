import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from luna.artwork import inspect_artwork


class ArtworkAuditTests(unittest.TestCase):
    def test_audit_inspects_all_embedded_pictures(self):
        first = SimpleNamespace(data=b"first", mime="image/jpeg")
        second = SimpleNamespace(data=b"", mime="image/png")
        audio = SimpleNamespace(pictures=[first, second])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "song.flac"
            path.write_bytes(b"audio")
            with patch("luna.artwork.File", return_value=audio):
                result = inspect_artwork(path)

        self.assertTrue(result.has_artwork)
        self.assertFalse(result.valid)
        self.assertEqual(len(result.entries), 2)
        self.assertTrue(result.entries[0].valid)
        self.assertFalse(result.entries[1].valid)
        self.assertIn("Artwork entry 2", result.reason)

    def test_multiple_valid_pictures_keep_first_entry_as_legacy_summary(self):
        first = SimpleNamespace(data=b"first", mime="image/jpeg")
        second = SimpleNamespace(data=b"second", mime="image/png")
        audio = SimpleNamespace(pictures=[first, second])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "song.flac"
            path.write_bytes(b"audio")
            with patch("luna.artwork.File", return_value=audio):
                result = inspect_artwork(path)

        self.assertTrue(result.valid)
        self.assertEqual(len(result.entries), 2)
        self.assertEqual(result.mime, "image/jpeg")
        self.assertEqual(result.entries[1].mime, "image/png")


if __name__ == "__main__":
    unittest.main()

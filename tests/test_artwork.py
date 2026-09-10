import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from luna.artwork import inspect_artwork

try:
    from PIL import Image
except ImportError:
    Image = None


# Tiny 2x3 PNG generated with Pillow; unlike the old b"first"/b"second" values,
# this is valid image data when Pillow-backed validation is enabled.
_VALID_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000002000000030802000000368849d6"
    "0000000b49444154789c6360c0020000150001aa6597c40000000049454e44ae426082"
)


class ArtworkAuditTests(unittest.TestCase):
    def test_audit_inspects_all_embedded_pictures(self):
        first = SimpleNamespace(data=_VALID_PNG, mime="image/png")
        second = SimpleNamespace(data=b"not-an-image", mime="image/jpeg")
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
        first = SimpleNamespace(data=_VALID_PNG, mime="image/png")
        second = SimpleNamespace(data=_VALID_PNG, mime="image/png")
        audio = SimpleNamespace(pictures=[first, second])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "song.flac"
            path.write_bytes(b"audio")
            with patch("luna.artwork.File", return_value=audio):
                result = inspect_artwork(path)

        self.assertTrue(result.valid)
        self.assertEqual(len(result.entries), 2)
        self.assertEqual(result.mime, "image/png")
        self.assertEqual(result.entries[1].mime, "image/png")

    @unittest.skipUnless(Image is not None, "Pillow is required for decoder exception testing")
    def test_unexpected_decoder_exception_is_not_swallowed(self):
        picture = SimpleNamespace(data=_VALID_PNG, mime="image/png")
        with patch("PIL.Image.open", side_effect=RuntimeError("unexpected decoder failure")):
            with self.assertRaisesRegex(RuntimeError, "unexpected decoder failure"):
                with patch("luna.artwork.File", return_value=SimpleNamespace(pictures=[picture])):
                    inspect_artwork(Path("song.flac"))


if __name__ == "__main__":
    unittest.main()

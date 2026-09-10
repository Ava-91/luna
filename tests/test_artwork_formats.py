import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mutagen.id3 import APIC, ID3
from mutagen.mp4 import MP4Cover

from luna.artwork import inspect_artwork

try:
    from PIL import Image
except ImportError:
    Image = None


_VALID_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000002000000030802000000368849d6"
    "0000000b49444154789c6360c0020000150001aa6597c40000000049454e44ae426082"
)


class ArtworkFormatTests(unittest.TestCase):
    def test_mp3_apic_artwork_is_inspected(self):
        tags = ID3()
        tags.add(APIC(encoding=3, mime="image/png", type=3, desc="Cover", data=_VALID_PNG))
        audio = SimpleNamespace(tags=tags)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "song.mp3"
            path.write_bytes(b"audio")
            with patch("luna.artwork.File", return_value=audio):
                result = inspect_artwork(path)

        self.assertTrue(result.has_artwork)
        self.assertEqual(len(result.entries), 1)
        self.assertEqual(result.mime, "image/png")
        self.assertTrue(result.valid)
        if Image is not None:
            self.assertEqual((result.width, result.height), (2, 3))

    def test_m4a_covr_artwork_is_inspected(self):
        cover = MP4Cover(_VALID_PNG, imageformat=MP4Cover.FORMAT_PNG)
        audio = SimpleNamespace(tags={"covr": [cover]})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "song.m4a"
            path.write_bytes(b"audio")
            with patch("luna.artwork.File", return_value=audio):
                result = inspect_artwork(path)

        self.assertTrue(result.has_artwork)
        self.assertEqual(len(result.entries), 1)
        self.assertEqual(result.mime, "image/png")
        self.assertTrue(result.valid)
        if Image is not None:
            self.assertEqual((result.width, result.height), (2, 3))


if __name__ == "__main__":
    unittest.main()

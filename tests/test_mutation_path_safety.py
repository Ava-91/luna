import tempfile
import unittest
from pathlib import Path

from mutagen.id3 import ID3

from luna.cli import apply_artwork_changes
from luna.metadata_apply import MetadataChange, apply_metadata_plan
from luna.paths import resolve_mutation_path
from luna.scanner import Track


class MutationPathSafetyTests(unittest.TestCase):
    def _mp3(self, path: Path) -> None:
        ID3().save(path)

    def _symlink(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

    def test_external_symlink_is_rejected_for_metadata_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = outside / "song.mp3"
            self._mp3(target)
            original = target.read_bytes()
            link = root / "link.mp3"
            self._symlink(link, target)

            results = apply_metadata_plan([MetadataChange(link, "title", None, "blocked")], True, root / "operations.json", root)

            self.assertFalse(results[0][1])
            self.assertIn("symlink", results[0][2].lower())
            self.assertEqual(target.read_bytes(), original)

    def test_internal_symlink_is_rejected_for_metadata_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "song.mp3"
            self._mp3(target)
            original = target.read_bytes()
            link = root / "link.mp3"
            self._symlink(link, target)

            results = apply_metadata_plan([MetadataChange(link, "title", None, "blocked")], True, root / "operations.json", root)

            self.assertFalse(results[0][1])
            self.assertIn("symlink", results[0][2].lower())
            self.assertEqual(target.read_bytes(), original)

    def test_nested_external_symlink_is_rejected_for_metadata_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = outside / "song.mp3"
            self._mp3(target)
            link2 = root / "link2.mp3"
            link1 = root / "link1.mp3"
            self._symlink(link2, target)
            self._symlink(link1, link2)
            original = target.read_bytes()

            results = apply_metadata_plan([MetadataChange(link1, "title", None, "blocked")], True, root / "operations.json", root)

            self.assertFalse(results[0][1])
            self.assertIn("symlink", results[0][2].lower())
            self.assertEqual(target.read_bytes(), original)

    def test_missing_symlink_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            link = root / "link.mp3"
            self._symlink(link, outside / "missing.mp3")

            with self.assertRaises(ValueError):
                resolve_mutation_path(root, link)

    def test_normal_file_metadata_mutation_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            self._mp3(path)

            results = apply_metadata_plan([MetadataChange(path, "title", None, "Working")], True, root / "operations.json", root)

            self.assertTrue(results[0][1])
            self.assertEqual(ID3(path).getall("TIT2")[0].text, ["Working"])

    def test_external_symlink_is_rejected_for_artwork_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = outside / "song.mp3"
            self._mp3(target)
            original = target.read_bytes()
            link = root / "link.mp3"
            self._symlink(link, target)
            cover = root / "cover.jpg"
            cover.write_bytes(b"not a real image")
            track = Track(link, "Song", "Artist", "Album")

            results = apply_artwork_changes(root, [track], True, root / "operations.json")

            self.assertTrue(results)
            self.assertFalse(results[0]["success"])
            self.assertIn("library", results[0]["error"].lower())
            self.assertEqual(target.read_bytes(), original)

    def test_normal_file_artwork_mutation_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            self._mp3(path)
            cover = root / "cover.jpg"
            cover.write_bytes(b"fake image data")
            track = Track(path, "Song", "Artist", "Album")

            results = apply_artwork_changes(root, [track], True, root / "operations.json")

            self.assertTrue(results)
            self.assertTrue(results[0]["success"])

    def test_artwork_candidate_symlink_outside_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = outside / "cover.jpg"
            target.write_bytes(b"outside")
            link = root / "cover.jpg"
            self._symlink(link, target)
            path = root / "song.mp3"
            self._mp3(path)
            track = Track(path, "Song", "Artist", "Album")

            results = apply_artwork_changes(root, [track], True, root / "operations.json")

            self.assertTrue(results)
            self.assertFalse(results[0]["success"])
            self.assertEqual(target.read_bytes(), b"outside")


if __name__ == "__main__":
    unittest.main()

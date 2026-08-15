import tempfile
import unittest
from pathlib import Path

from luna.duplicates import find_duplicates, hash_file
from luna.scanner import Track


class DuplicateDetectionTests(unittest.TestCase):
    def test_identical_files_form_one_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.mp3"
            second = root / "second.mp3"
            first.write_bytes(b"same audio")
            second.write_bytes(b"same audio")

            tracks = [Track(first, "A", "Artist", "Album"), Track(second, "B", "Artist", "Album")]
            groups = find_duplicates(tracks)

            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0].size, 2)
            self.assertEqual(groups[0].digest, hash_file(first))

    def test_distinct_files_are_not_grouped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.mp3"
            second = root / "second.mp3"
            first.write_bytes(b"one")
            second.write_bytes(b"two")

            tracks = [Track(first, None, None, None), Track(second, None, None, None)]
            self.assertEqual(find_duplicates(tracks), [])

    def test_duplicate_detection_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.mp3"
            second = root / "second.mp3"
            first.write_bytes(b"same")
            second.write_bytes(b"same")
            before = (first.read_bytes(), second.read_bytes())

            find_duplicates([Track(first, None, None, None), Track(second, None, None, None)])

            self.assertEqual((first.read_bytes(), second.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()

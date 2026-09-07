import tempfile
import unittest
from pathlib import Path

from luna.duplicates import find_probable_duplicates
from luna.scanner import Track


class ProbableDuplicateGroupTests(unittest.TestCase):
    def _track(self, root, name, album="Album", year=2020, size=100, track_number=1, disc_number=1):
        path = root / name
        path.write_bytes(b"x" * size)
        return Track(path, "Song", "Artist", album, track_number, disc_number=disc_number, year=year, size=size)

    def test_two_strong_matches_form_one_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._track(root, "a.mp3")
            second = self._track(root, "b.mp3")
            groups = find_probable_duplicates([second, first])
            self.assertEqual(len(groups), 1)
            self.assertEqual([track.path.name for track in groups[0].tracks], ["a.mp3", "b.mp3"])
            self.assertEqual(groups[0].confidence, 0.95)
            self.assertIn("artist matches", groups[0].reasons)
            self.assertIn("title matches", groups[0].reasons)
            self.assertIn("album matches", groups[0].reasons)

    def test_weak_third_track_is_not_included_in_strong_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._track(root, "a.mp3")
            second = self._track(root, "b.mp3")
            third = self._track(root, "c.mp3", album="Different", year=2021, size=999, track_number=2, disc_number=2)
            groups = find_probable_duplicates([third, second, first])
            self.assertEqual(len(groups), 1)
            self.assertEqual({track.path.name for track in groups[0].tracks}, {"a.mp3", "b.mp3"})
            self.assertEqual(groups[0].confidence, 0.95)

    def test_two_separate_duplicate_clusters_in_one_bucket(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self._track(root, "a.mp3", album="Album A", size=100)
            b = self._track(root, "b.mp3", album="Album A", size=100)
            c = self._track(root, "c.mp3", album="Album B", size=200, year=2021)
            d = self._track(root, "d.mp3", album="Album B", size=200, year=2021)
            groups = find_probable_duplicates([d, c, b, a])
            self.assertEqual(len(groups), 2)
            self.assertEqual({track.path.name for track in groups[0].tracks}, {"a.mp3", "b.mp3"})
            self.assertEqual({track.path.name for track in groups[1].tracks}, {"c.mp3", "d.mp3"})

    def test_same_artist_title_different_album_uses_actual_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._track(root, "a.mp3", album="Album A")
            second = self._track(root, "b.mp3", album="Album B", year=2021, size=101, track_number=2, disc_number=2)
            groups = find_probable_duplicates([first, second])
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0].confidence, 0.60)
            self.assertNotIn("album matches", groups[0].reasons)

    def test_missing_metadata_does_not_create_probable_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = Track(root / "a.mp3", "Song", None, "Album", 1, size=100)
            second = Track(root / "b.mp3", "Song", None, "Album", 1, size=100)
            first.path.write_bytes(b"x" * 100)
            second.path.write_bytes(b"x" * 100)
            self.assertEqual(find_probable_duplicates([first, second]), [])

    def test_different_sizes_can_still_match_when_other_signals_are_strong(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._track(root, "a.mp3", size=100)
            second = self._track(root, "b.mp3", size=101)
            groups = find_probable_duplicates([first, second])
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0].confidence, 0.85)
            self.assertNotIn("file size matches", groups[0].reasons)

    def test_single_track_is_not_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(find_probable_duplicates([self._track(root, "a.mp3")]), [])

    def test_output_is_deterministically_ordered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tracks = [self._track(root, name) for name in ("z.mp3", "y.mp3", "x.mp3")]
            groups = find_probable_duplicates(tracks)
            self.assertEqual([track.path.name for track in groups[0].tracks], ["x.mp3", "y.mp3", "z.mp3"])
            self.assertEqual(groups[0].reasons, ("artist matches", "title matches", "album matches", "track number matches", "disc number matches", "file size matches", "year matches"))


if __name__ == "__main__":
    unittest.main()

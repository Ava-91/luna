import tempfile
import unittest
import wave
from pathlib import Path

from luna.apply import apply_rename_plan
from luna.planner import RenamePlanItem
from luna.scanner import scan_library


class FilesystemIntegrationTests(unittest.TestCase):
    def _wav(self, path, frames=b"\x00\x00" * 32):
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(frames)

    def test_scan_reads_real_recursive_audio_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "nested"
            nested.mkdir()
            self._wav(root / "one.wav")
            self._wav(nested / "two.wav")
            (root / "notes.txt").write_text("ignore me", encoding="utf-8")

            tracks = scan_library(root, workers=1)

            self.assertEqual([track.path.name for track in tracks], ["one.wav", "two.wav"])
            self.assertTrue(all(track.path.exists() for track in tracks))

    def test_duplicate_analysis_works_on_real_scanned_files(self):
        from luna.duplicates import find_duplicates

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._wav(root / "one.wav")
            self._wav(root / "two.wav")
            tracks = scan_library(root, workers=1)

            groups = find_duplicates(tracks)

            self.assertEqual(len(groups), 1)
            self.assertEqual({track.path.name for track in groups[0].tracks}, {"one.wav", "two.wav"})

    def test_real_filesystem_rename_apply_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "old.wav"
            destination = root / "new.wav"
            self._wav(source)
            plan = [RenamePlanItem(source, destination, "change", "integration test")]

            results = apply_rename_plan(plan, True, root / "operations.json")

            self.assertTrue(results[0].success)
            self.assertFalse(source.exists())
            self.assertTrue(destination.exists())

            from luna.backup import rollback
            rollback_results = rollback(root / "operations.json", True)
            self.assertTrue(rollback_results[0][0])
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()

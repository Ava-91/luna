import json
import tempfile
import unittest
import wave
from pathlib import Path

from mutagen import File

from luna.metadata_apply import apply_metadata_plan, build_metadata_plan
from luna.scanner import inspect_file


class MetadataApplyTests(unittest.TestCase):
    def _tagged_wav(self, directory: Path) -> Path:
        path = directory / "track.wav"
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(8000)
            handle.writeframes(b"\x00\x00" * 800)
        audio = File(path, easy=True)
        self.assertIsNotNone(audio)
        audio.add_tags()
        audio.tags["album"] = [" "]
        audio.tags["title"] = ["  Song  "]
        audio.save()
        return path

    def test_none_normalization_is_planned_applied_logged_and_rolled_back(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._tagged_wav(root)
            track = inspect_file(path)

            album_change = next(item for item in __import__("luna.normalize", fromlist=["normalize_track"]).normalize_track(track) if item.field == "album")
            self.assertEqual(album_change.original, " ")
            self.assertIsNone(album_change.normalized)
            self.assertTrue(album_change.changed)

            plan = build_metadata_plan([track])
            change = next(item for item in plan if item.field == "album")
            self.assertEqual(change.old, " ")
            self.assertIsNone(change.new)

            log_path = root / "operation-log.json"
            results = apply_metadata_plan(plan, confirm=True, log_path=log_path, root=root)
            album_result = next(result for item, result, _ in results if item.field == "album")
            self.assertTrue(album_result)

            audio = File(path, easy=True)
            self.assertIsNotNone(audio)
            self.assertNotIn("album", audio.tags)

            log = json.loads(log_path.read_text(encoding="utf-8"))
            album_operation = next(op for op in log["operations"] if op["field"] == "album")
            self.assertEqual(album_operation["old_value"], " ")
            self.assertIsNone(album_operation["new_value"])
            self.assertEqual(album_operation["status"], "completed")

            from luna.backup import rollback

            rollback_results = rollback(log_path, confirm=True, root=root)
            self.assertTrue(all(result[0] for result in rollback_results))

            restored = File(path, easy=True)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.tags["album"], [" "])

    def test_non_none_normalization_still_applies_and_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self._tagged_wav(root)
            track = inspect_file(path)
            plan = build_metadata_plan([track])
            change = next(item for item in plan if item.field == "title")
            self.assertEqual(change.old, "  Song  ")
            self.assertEqual(change.new, "Song")

            log_path = root / "operation-log.json"
            results = apply_metadata_plan([change], confirm=True, log_path=log_path, root=root)
            self.assertTrue(results[0][1])
            audio = File(path, easy=True)
            self.assertEqual(audio.tags["title"], ["Song"])

            from luna.backup import rollback

            rollback_results = rollback(log_path, confirm=True, root=root)
            self.assertTrue(all(result[0] for result in rollback_results))
            restored = File(path, easy=True)
            self.assertEqual(restored.tags["title"], ["  Song  "])


if __name__ == "__main__":
    unittest.main()

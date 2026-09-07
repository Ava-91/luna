import json
import tempfile
import unittest
import wave
from pathlib import Path

from mutagen import File

from luna.backup import rollback
from luna.metadata_apply import apply_metadata_plan, build_metadata_plan
from luna.normalize import normalize_track
from luna.scanner import Track


class MetadataNoneApplicationTests(unittest.TestCase):
    def _wav(self, path: Path):
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(b"\x00\x00" * 32)
        audio = File(path, easy=True)
        self.assertIsNotNone(audio)
        if audio.tags is None:
            audio.add_tags()
        audio.tags["title"] = ["  Song  "]
        audio.tags["album"] = [" "]
        audio.save()

    def _track(self, path: Path):
        return Track(path, "  Song  ", "Artist", " ", format="wav")

    def test_whitespace_normalizes_to_none_and_plan_includes_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "song.wav"
            self._wav(path)
            values = {item.field: item for item in normalize_track(self._track(path))}
            self.assertTrue(values["album"].changed)
            self.assertIsNone(values["album"].normalized)

            plan = build_metadata_plan([self._track(path)])
            album_change = next(item for item in plan if item.field == "album")
            self.assertEqual(album_change.old, " ")
            self.assertIsNone(album_change.new)

    def test_apply_clear_logs_none_and_rollback_restores_original_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.wav"
            log_path = root / "operations.json"
            self._wav(path)
            plan = build_metadata_plan([self._track(path)])

            results = apply_metadata_plan(plan, confirm=True, log_path=log_path, root=root)
            self.assertTrue(all(ok for _, ok, _ in results))

            audio = File(path, easy=True)
            self.assertIsNotNone(audio)
            self.assertNotIn("album", audio.tags)
            self.assertEqual(audio.tags["title"], ["Song"])

            log = json.loads(log_path.read_text(encoding="utf-8"))
            album_operation = next(op for op in log["operations"] if op["field"] == "album")
            self.assertEqual(album_operation["old_value"], " ")
            self.assertIsNone(album_operation["new_value"])

            rollback_results = rollback(log_path, confirm=True)
            self.assertTrue(all(ok for ok, *_ in rollback_results))

            restored = File(path, easy=True)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.tags["album"], [" "])
            self.assertEqual(restored.tags["title"], ["  Song  "])


if __name__ == "__main__":
    unittest.main()

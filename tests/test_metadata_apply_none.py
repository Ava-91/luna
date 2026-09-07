import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mutagen.easyid3 import EasyID3

from luna.backup import rollback
from luna.metadata_apply import apply_metadata_plan, build_metadata_plan
from luna.normalize import normalize_track
from luna.scanner import Track


class _EasyAudio:
    def __init__(self, path: Path):
        self.path = path
        self.tags = EasyID3(path)

    def add_tags(self):
        return None

    def save(self):
        self.tags.save(self.path)


class MetadataNoneApplicationTests(unittest.TestCase):
    def _tagged_file(self, path: Path):
        tags = EasyID3()
        tags["title"] = ["  Song  "]
        tags["album"] = [" "]
        tags.save(path)

    def _track(self, path: Path):
        return Track(path, "  Song  ", "Artist", " ", format="mp3")

    def test_whitespace_normalizes_to_none_and_plan_includes_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "song.mp3"
            self._tagged_file(path)
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
            path = root / "song.mp3"
            log_path = root / "operations.json"
            self._tagged_file(path)
            plan = build_metadata_plan([self._track(path)])

            with patch("luna.metadata_apply.File", side_effect=lambda target, easy=True: _EasyAudio(target)):
                results = apply_metadata_plan(plan, confirm=True, log_path=log_path, root=root)
            self.assertTrue(all(ok for _, ok, _ in results))

            audio = EasyID3(path)
            self.assertNotIn("album", audio)
            self.assertEqual(audio["title"], ["Song"])

            log = json.loads(log_path.read_text(encoding="utf-8"))
            album_operation = next(op for op in log["operations"] if op["field"] == "album")
            self.assertEqual(album_operation["old_value"], " ")
            self.assertIsNone(album_operation["new_value"])

            with patch("mutagen.File", side_effect=lambda target, easy=True: _EasyAudio(target)):
                rollback_results = rollback(log_path, confirm=True)
            self.assertTrue(all(ok for ok, *_ in rollback_results))

            restored = EasyID3(path)
            self.assertEqual(restored["album"], [" "])
            self.assertEqual(restored["title"], ["  Song  "])


if __name__ == "__main__":
    unittest.main()

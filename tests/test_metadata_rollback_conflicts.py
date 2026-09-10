import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from luna.backup import OperationLog, rollback


class _FakeAudio:
    def __init__(self, value):
        self.tags = {} if value is None else {"title": [value]}
        self.saved = False

    def add_tags(self):
        return None

    def save(self):
        self.saved = True


class MetadataRollbackConflictTests(unittest.TestCase):
    def _pending_log(self, root, old, new):
        log = OperationLog(root / "operations.json", root)
        log.record_metadata(root / "song.mp3", "title", old, new)
        log.save()
        return log

    def test_pending_without_mutation_does_not_rewrite_old_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            log = self._pending_log(root, "old", "new")
            audio = _FakeAudio("old")
            with patch("mutagen.File", return_value=audio):
                result = rollback(log.path, True)
            self.assertEqual(result, [(True, str(path), "title")])
            self.assertEqual(audio.tags["title"], ["old"])
            self.assertFalse(audio.saved)

    def test_pending_after_mutation_restores_old_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            log = self._pending_log(root, "old", "new")
            audio = _FakeAudio("new")
            with patch("mutagen.File", return_value=audio):
                result = rollback(log.path, True)
            self.assertEqual(result, [(True, str(path), "title")])
            self.assertEqual(audio.tags["title"], ["old"])
            self.assertTrue(audio.saved)

    def test_pending_external_change_is_reported_as_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            log = self._pending_log(root, "old", "new")
            audio = _FakeAudio("external")
            with patch("mutagen.File", return_value=audio):
                result = rollback(log.path, True)
            self.assertFalse(result[0][0])
            self.assertIn("conflict", result[0][2].lower())
            self.assertEqual(audio.tags["title"], ["external"])
            self.assertFalse(audio.saved)

    def test_pending_clear_after_mutation_restores_old_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            log = self._pending_log(root, "old", None)
            audio = _FakeAudio(None)
            with patch("mutagen.File", return_value=audio):
                result = rollback(log.path, True)
            self.assertEqual(result, [(True, str(path), "title")])
            self.assertEqual(audio.tags["title"], ["old"])
            self.assertTrue(audio.saved)

    def test_completed_metadata_rollback_keeps_existing_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            log = OperationLog(root / "operations.json", root)
            index = log.record_metadata(path, "title", "old", "new")
            log.mark_completed(index)
            audio = _FakeAudio("external")
            with patch("mutagen.File", return_value=audio):
                result = rollback(log.path, True)
            self.assertEqual(result, [(True, str(path), "title")])
            self.assertEqual(audio.tags["title"], ["old"])
            self.assertTrue(audio.saved)


if __name__ == "__main__":
    unittest.main()

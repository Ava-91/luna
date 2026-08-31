import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from luna.backup import OperationLog, rollback


class OperationLogSafetyTests(unittest.TestCase):
    def test_rollback_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "operations.json"
            log_path.write_text("[]", encoding="utf-8")
            with self.assertRaises(PermissionError):
                rollback(log_path)

    def test_filename_rollback_restores_original_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "old.mp3"
            changed = root / "new.mp3"
            changed.write_bytes(b"audio")

            log = OperationLog(root / "operations.json")
            log.record("rename", original, changed)
            log.save()

            results = rollback(log.path, True)

            self.assertEqual(results, [(True, str(changed), str(original))])
            self.assertTrue(original.exists())
            self.assertFalse(changed.exists())

    def test_rollback_processes_operations_in_reverse_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first.mp3"
            second = root / "second.mp3"
            first_changed = root / "first-renamed.mp3"
            second_changed = root / "second-renamed.mp3"
            first_changed.write_bytes(b"one")
            second_changed.write_bytes(b"two")

            log = OperationLog(root / "operations.json")
            log.record("rename", first, first_changed)
            log.record("rename", second, second_changed)
            log.save()

            results = rollback(log.path, True)

            self.assertEqual(results[0][1:], (str(second_changed), str(second)))
            self.assertEqual(results[1][1:], (str(first_changed), str(first)))

    def test_rollback_refuses_to_overwrite_existing_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "old.mp3"
            changed = root / "new.mp3"
            original.write_bytes(b"original")
            changed.write_bytes(b"changed")

            log = OperationLog(root / "operations.json")
            log.record("rename", original, changed)
            log.save()

            results = rollback(log.path, True)

            self.assertEqual(results, [(False, str(changed), "Original destination already exists.")])
            self.assertEqual(original.read_bytes(), b"original")
            self.assertEqual(changed.read_bytes(), b"changed")

    def test_rollback_reports_missing_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "old.mp3"
            changed = root / "new.mp3"

            log = OperationLog(root / "operations.json")
            log.record("rename", original, changed)
            log.save()

            results = rollback(log.path, True)

            self.assertEqual(results, [(False, str(changed), "Changed file is missing.")])

    def test_metadata_rollback_restores_previous_value(self):
        class FakeAudio:
            def __init__(self):
                self.tags = {"title": ["new title"]}
                self.saved = False

            def save(self):
                self.saved = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio_path = root / "song.mp3"
            audio_path.write_bytes(b"audio")
            fake_audio = FakeAudio()

            log = OperationLog(root / "operations.json")
            log.record_metadata(audio_path, "title", "old title", "new title")
            log.save()

            with patch("mutagen.File", return_value=fake_audio):
                results = rollback(log.path, True)

            self.assertEqual(results, [(True, str(audio_path), "title")])
            self.assertEqual(fake_audio.tags["title"], ["old title"])
            self.assertTrue(fake_audio.saved)

    def test_saved_log_contains_all_operation_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "operations.json"
            log = OperationLog(log_path)
            log.record_metadata(root / "song.mp3", "title", "old", "new")
            log.save()

            data = json.loads(log_path.read_text(encoding="utf-8"))

            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["action"], "metadata")
            self.assertEqual(data[0]["field"], "title")
            self.assertEqual(data[0]["old_value"], "old")
            self.assertEqual(data[0]["new_value"], "new")
            self.assertIn("timestamp", data[0])


if __name__ == "__main__":
    unittest.main()

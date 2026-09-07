import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from luna.backup import OperationLog, rollback


class OperationLogSafetyTests(unittest.TestCase):
    def _complete(self, log, index):
        log.mark_completed(index)

    def test_rollback_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "operations.json"
            log_path.write_text("[]", encoding="utf-8")
            with self.assertRaises(PermissionError):
                rollback(log_path)

    def test_filename_rollback_restores_original_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, changed = root / "old.mp3", root / "new.mp3"
            changed.write_bytes(b"audio")
            log = OperationLog(root / "operations.json", root)
            index = log.record("rename", original, changed)
            self._complete(log, index)

            results = rollback(log.path, True)

            self.assertEqual(results, [(True, str(changed), str(original))])
            self.assertTrue(original.exists())
            self.assertFalse(changed.exists())

    def test_rollback_processes_operations_in_reverse_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root / "first.mp3", root / "second.mp3"
            first_changed, second_changed = root / "first-renamed.mp3", root / "second-renamed.mp3"
            first_changed.write_bytes(b"one")
            second_changed.write_bytes(b"two")
            log = OperationLog(root / "operations.json", root)
            first_index = log.record("rename", first, first_changed)
            second_index = log.record("rename", second, second_changed)
            self._complete(log, first_index)
            self._complete(log, second_index)

            results = rollback(log.path, True)

            self.assertEqual(results[0][1:], (str(second_changed), str(second)))
            self.assertEqual(results[1][1:], (str(first_changed), str(first)))

    def test_rollback_refuses_to_overwrite_existing_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, changed = root / "old.mp3", root / "new.mp3"
            original.write_bytes(b"original")
            changed.write_bytes(b"changed")
            log = OperationLog(root / "operations.json", root)
            index = log.record("rename", original, changed)
            self._complete(log, index)

            results = rollback(log.path, True)

            self.assertEqual(results, [(False, str(original), "Original destination already exists.")])
            self.assertEqual(original.read_bytes(), b"original")
            self.assertEqual(changed.read_bytes(), b"changed")

    def test_rollback_reports_missing_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, changed = root / "old.mp3", root / "new.mp3"
            log = OperationLog(root / "operations.json", root)
            index = log.record("rename", original, changed)
            self._complete(log, index)

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
            log = OperationLog(root / "operations.json", root)
            index = log.record_metadata(audio_path, "title", "old title", "new title")
            self._complete(log, index)

            with patch("mutagen.File", return_value=fake_audio):
                results = rollback(log.path, True)

            self.assertEqual(results, [(True, str(audio_path), "title")])
            self.assertEqual(fake_audio.tags["title"], ["old title"])
            self.assertTrue(fake_audio.saved)

    def test_artwork_rollback_restores_full_original_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "song.mp3"
            backup = root / "backups" / "song.mp3.bak"
            source.write_bytes(b"modified artwork file")
            backup.parent.mkdir()
            backup.write_bytes(b"original audio with original artwork")
            log = OperationLog(root / "operations.json", root)
            index = log.record_artwork(source, root / "cover.jpg", backup)
            self._complete(log, index)

            results = rollback(log.path, True)

            self.assertEqual(results, [(True, str(source), str(backup))])
            self.assertEqual(source.read_bytes(), b"original audio with original artwork")

    def test_saved_log_is_durable_transaction_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "operations.json"
            log = OperationLog(log_path, root)
            index = log.record_metadata(root / "song.mp3", "title", "old", "new")
            log.save()

            data = json.loads(log_path.read_text(encoding="utf-8"))

            self.assertEqual(data["version"], 2)
            self.assertEqual(data["state"], "prepared")
            self.assertTrue(data["transaction_id"])
            self.assertEqual(data["library_root"], str(root.resolve()))
            self.assertEqual(data["operations"][0]["action"], "metadata")
            self.assertEqual(data["operations"][0]["status"], "pending")
            self.assertEqual(data["operations"][0]["field"], "title")
            self.assertEqual(data["operations"][0]["old_value"], "old")
            self.assertEqual(data["operations"][0]["new_value"], "new")
            self.assertEqual(index, 0)

            log.mark_completed(index)
            data = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(data["operations"][0]["status"], "completed")
            log.finalize()
            data = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(data["state"], "committed")

    def test_journal_write_failure_happens_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "operations.json"
            log = OperationLog(log_path, root)
            log.record("rename", root / "old.mp3", root / "new.mp3")
            with patch("pathlib.Path.open", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    log.save()
            self.assertFalse((root / "old.mp3").exists())
            self.assertFalse((root / "new.mp3").exists())
            self.assertFalse(log_path.exists())

    def test_recovery_from_rename_interruption_after_one_move(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "a.txt", root / "b.txt"
            a.write_bytes(b"A")
            b.write_bytes(b"B")
            temp_a = root / ".a.txt.luna-tmp-a"
            a.rename(temp_a)
            log = OperationLog(root / "operations.json", root)
            first = log.record("rename", a, b, backup_path=temp_a)
            log.save()
            results = rollback(log.path, True)

            self.assertTrue(results[0][0])
            self.assertEqual(a.read_bytes(), b"A")
            self.assertEqual(b.read_bytes(), b"B")

    def test_recovery_after_destination_move_before_completion_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "a.txt", root / "b.txt"
            a.write_bytes(b"A")
            b.unlink()
            log = OperationLog(root / "operations.json", root)
            log.record("rename", a, b, backup_path=root / ".a.tmp")
            log.save()
            a.rename(b)

            results = rollback(log.path, True)

            self.assertTrue(results[0][0])
            self.assertEqual(a.read_bytes(), b"A")
            self.assertFalse(b.exists())

    def test_pending_metadata_is_not_falsely_reported_as_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            log = OperationLog(root / "operations.json", root)
            log.record_metadata(path, "title", "old", "new")
            log.save()

            results = rollback(log.path, True)

            self.assertEqual(results, [])
            self.assertTrue(path.exists())

    def test_legacy_log_requires_explicit_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changed = root / "new.mp3"
            changed.write_bytes(b"audio")
            log_path = root / "operations.json"
            log_path.write_text(json.dumps([{
                "action": "rename",
                "source": str(root / "old.mp3"),
                "destination": str(changed),
                "timestamp": "2026-01-01T00:00:00+00:00",
            }]), encoding="utf-8")

            with self.assertRaises(ValueError):
                rollback(log_path, True)
            results = rollback(log_path, True, root)
            self.assertTrue(results[0][0])
            self.assertTrue((root / "old.mp3").exists())
            self.assertFalse(changed.exists())


if __name__ == "__main__":
    unittest.main()

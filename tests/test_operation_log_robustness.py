import json
import tempfile
import unittest
from pathlib import Path

from luna.backup import rollback


class OperationLogRobustnessTests(unittest.TestCase):
    def _write(self, root, data):
        path = root / "operations.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_empty_log_is_a_safe_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(rollback(self._write(Path(tmp), []), True), [])

    def test_non_array_log_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                rollback(self._write(Path(tmp), {"action": "rename"}), True)

    def test_missing_operation_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                rollback(self._write(Path(tmp), [{"action": "rename"}]), True)

    def test_unknown_operation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = [{"action": "mystery", "source": "a", "destination": "b", "timestamp": "now"}]
            with self.assertRaises(ValueError):
                rollback(self._write(Path(tmp), data), True)

    def test_artwork_operation_is_not_treated_as_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = [{"action": "artwork", "source": str(root / "a.mp3"), "destination": str(root / "cover.jpg"), "timestamp": "now"}]
            results = rollback(self._write(root, data), True)
            self.assertEqual(results, [(False, str(root / "a.mp3"), "Artwork rollback is not supported.")])


if __name__ == "__main__":
    unittest.main()

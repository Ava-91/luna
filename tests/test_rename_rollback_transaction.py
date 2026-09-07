import tempfile
import unittest
from pathlib import Path

from luna.apply import apply_rename_plan
from luna.backup import OperationLog, rollback
from luna.planner import RenamePlanItem


class RenameRollbackTransactionTests(unittest.TestCase):
    def _write(self, path, data):
        path.write_bytes(data)

    def _snapshot(self, root):
        return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file() and path.name != "operations.json"}

    def test_two_file_cycle_round_trips_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root / "a.txt", root / "b.txt"
            self._write(first, b"A")
            self._write(second, b"B")
            before = self._snapshot(root)
            log_path = root / "operations.json"
            plan = [
                RenamePlanItem(first, second, "change", "cycle"),
                RenamePlanItem(second, first, "change", "cycle"),
            ]

            self.assertTrue(all(item.success for item in apply_rename_plan(plan, True, log_path, root)))
            results = rollback(log_path, True)

            self.assertTrue(all(result[0] for result in results))
            self.assertEqual(self._snapshot(root), before)
            self.assertFalse(any(root.glob("*.luna-rollback-*")))

    def test_three_file_cycle_round_trips_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [root / name for name in ("a.txt", "b.txt", "c.txt")]
            for path, data in zip(paths, (b"A", b"B", b"C")):
                self._write(path, data)
            before = self._snapshot(root)
            log_path = root / "operations.json"
            plan = [
                RenamePlanItem(paths[0], paths[1], "change", "cycle"),
                RenamePlanItem(paths[1], paths[2], "change", "cycle"),
                RenamePlanItem(paths[2], paths[0], "change", "cycle"),
            ]

            self.assertTrue(all(item.success for item in apply_rename_plan(plan, True, log_path, root)))
            results = rollback(log_path, True)

            self.assertTrue(all(result[0] for result in results))
            self.assertEqual(self._snapshot(root), before)

    def test_mixed_cycle_and_independent_rename_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b, c = [root / name for name in ("a.txt", "b.txt", "c.txt")]
            for path, data in zip((a, b, c), (b"A", b"B", b"C")):
                self._write(path, data)
            destination = root / "d.txt"
            before = self._snapshot(root)
            log_path = root / "operations.json"
            plan = [
                RenamePlanItem(a, b, "change", "mixed"),
                RenamePlanItem(b, a, "change", "mixed"),
                RenamePlanItem(c, destination, "change", "mixed"),
            ]

            self.assertTrue(all(item.success for item in apply_rename_plan(plan, True, log_path, root)))
            results = rollback(log_path, True)

            self.assertTrue(all(result[0] for result in results))
            self.assertEqual(self._snapshot(root), before)

    def test_rollback_missing_path_does_not_mutate_remaining_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, changed = root / "old.txt", root / "new.txt"
            changed.write_bytes(b"changed")
            log_path = root / "operations.json"
            log = OperationLog(log_path, root)
            log.record("rename", original, changed)
            log.save()
            changed.unlink()

            results = rollback(log_path, True)

            self.assertFalse(results[0][0])
            self.assertFalse(original.exists())

    def test_rollback_collision_does_not_overwrite_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original, changed = root / "old.txt", root / "new.txt"
            original.write_bytes(b"original")
            changed.write_bytes(b"changed")
            log_path = root / "operations.json"
            log = OperationLog(log_path, root)
            log.record("rename", original, changed)
            log.save()

            results = rollback(log_path, True)

            self.assertFalse(results[0][0])
            self.assertEqual(original.read_bytes(), b"original")
            self.assertEqual(changed.read_bytes(), b"changed")


if __name__ == "__main__":
    unittest.main()

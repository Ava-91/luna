import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

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

            self.assertEqual(
                sorted(track.path.name for track in tracks),
                ["one.wav", "two.wav"],
            )
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

            results = apply_rename_plan(plan, True, root / "operations.json", root)

            self.assertTrue(results[0].success)
            self.assertFalse(source.exists())
            self.assertTrue(destination.exists())

            from luna.backup import rollback
            rollback_results = rollback(root / "operations.json", True)
            self.assertTrue(rollback_results[0][0])
            self.assertTrue(source.exists())
            self.assertFalse(destination.exists())

    def test_real_filesystem_two_file_rename_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.wav"
            second = root / "b.wav"
            self._wav(first, b"A" * 64)
            self._wav(second, b"B" * 64)
            original_first = first.read_bytes()
            original_second = second.read_bytes()
            plan = [
                RenamePlanItem(first, second, "change", "cycle"),
                RenamePlanItem(second, first, "change", "cycle"),
            ]

            results = apply_rename_plan(plan, True, root=root)

            self.assertTrue(all(result.success for result in results))
            self.assertEqual(first.read_bytes(), original_second)
            self.assertEqual(second.read_bytes(), original_first)
            self.assertFalse(any(root.glob("*.luna-tmp-*")))

    def test_real_filesystem_three_file_rename_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [root / name for name in ("a.wav", "b.wav", "c.wav")]
            payloads = [b"A" * 64, b"B" * 64, b"C" * 64]
            for path, payload in zip(paths, payloads):
                self._wav(path, payload)
            original = [path.read_bytes() for path in paths]
            plan = [
                RenamePlanItem(paths[0], paths[1], "change", "cycle"),
                RenamePlanItem(paths[1], paths[2], "change", "cycle"),
                RenamePlanItem(paths[2], paths[0], "change", "cycle"),
            ]

            results = apply_rename_plan(plan, True, root=root)

            self.assertTrue(all(result.success for result in results))
            self.assertEqual(paths[0].read_bytes(), original[2])
            self.assertEqual(paths[1].read_bytes(), original[0])
            self.assertEqual(paths[2].read_bytes(), original[1])
            self.assertFalse(any(root.glob("*.luna-tmp-*")))

    def test_rename_failure_rolls_back_completed_moves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.wav"
            second = root / "b.wav"
            self._wav(first, b"A" * 64)
            self._wav(second, b"B" * 64)
            original_first = first.read_bytes()
            original_second = second.read_bytes()
            plan = [
                RenamePlanItem(first, second, "change", "cycle"),
                RenamePlanItem(second, first, "change", "cycle"),
            ]
            original_rename = Path.rename
            calls = 0

            def rename_with_failure(path, target):
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise OSError("simulated rename failure")
                return original_rename(path, target)

            log_path = root / "operations.json"
            with patch.object(Path, "rename", new=rename_with_failure):
                results = apply_rename_plan(plan, True, log_path, root)

            self.assertTrue(all(not result.success for result in results))
            self.assertIn("rolled back", results[0].error.lower())
            self.assertEqual(first.read_bytes(), original_first)
            self.assertEqual(second.read_bytes(), original_second)
            self.assertFalse(log_path.exists())
            self.assertFalse(any(root.glob("*.luna-tmp-*")))

    def test_external_symlink_is_rejected_by_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = outside / "song.wav"
            self._wav(target, b"outside" * 16)
            link = root / "link.wav"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            result = apply_rename_plan([RenamePlanItem(link, root / "new.wav", "change", "symlink")], True, root=root)

            self.assertFalse(result[0].success)
            self.assertIn("symlink", result[0].error.lower())
            self.assertEqual(target.read_bytes(), target.read_bytes())
            self.assertTrue(link.is_symlink())

    def test_internal_symlink_is_rejected_by_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "real.wav"
            self._wav(target)
            link = root / "link.wav"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            result = apply_rename_plan([RenamePlanItem(link, root / "new.wav", "change", "symlink")], True, root=root)

            self.assertFalse(result[0].success)
            self.assertIn("symlink", result[0].error.lower())
            self.assertTrue(target.exists())
            self.assertTrue(link.is_symlink())

    def test_nested_external_symlink_is_rejected_by_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = outside / "song.wav"
            self._wav(target)
            second = root / "second.wav"
            first = root / "first.wav"
            try:
                second.symlink_to(target)
                first.symlink_to(second)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            result = apply_rename_plan([RenamePlanItem(first, root / "new.wav", "change", "symlink")], True, root=root)

            self.assertFalse(result[0].success)
            self.assertIn("symlink", result[0].error.lower())
            self.assertTrue(target.exists())

    def test_missing_symlink_target_is_rejected_by_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "library"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            missing = outside / "missing.wav"
            link = root / "link.wav"
            try:
                link.symlink_to(missing)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            result = apply_rename_plan([RenamePlanItem(link, root / "new.wav", "change", "symlink")], True, root=root)

            self.assertFalse(result[0].success)
            self.assertIn("symlink", result[0].error.lower())
            self.assertTrue(link.is_symlink())

    def test_normal_file_rename_still_works_with_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "old.wav"
            destination = root / "new.wav"
            self._wav(source)

            result = apply_rename_plan([RenamePlanItem(source, destination, "change", "normal")], True, root=root)

            self.assertTrue(result[0].success)
            self.assertTrue(destination.exists())
            self.assertFalse(source.exists())


if __name__ == "__main__":
    unittest.main()

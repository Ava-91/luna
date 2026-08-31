import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from luna import cli


class CLISafetyTests(unittest.TestCase):
    def test_missing_path_is_rejected(self):
        with self.assertRaises(SystemExit) as exc:
            cli.main(["scan", "/definitely/not/a/real/luna-path"])
        self.assertEqual(exc.exception.code, 2)

    def test_apply_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as exc:
                cli.main(["apply", tmp])
        self.assertEqual(exc.exception.code, 2)

    def test_rollback_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "operations.json"
            log.write_text("[]", encoding="utf-8")
            with self.assertRaises(SystemExit) as exc:
                cli.main(["rollback", str(log)])
        self.assertEqual(exc.exception.code, 2)

    def test_apply_rejects_conflicting_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as exc:
                cli.main(["apply", tmp, "--confirm", "--metadata", "--artwork"])
        self.assertEqual(exc.exception.code, 2)

    def test_confirmed_apply_dispatches_selected_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(cli, "load_tracks", return_value=[]), \
                 patch.object(cli, "apply_metadata_plan", return_value=[]) as apply_metadata, \
                 patch.object(cli, "build_metadata_plan", return_value=[]):
                cli.main(["apply", tmp, "--confirm", "--metadata"])
        apply_metadata.assert_called_once()

    def test_confirmed_rollback_dispatches_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "operations.json"
            log.write_text("[]", encoding="utf-8")
            with patch.object(cli, "rollback", return_value=[]) as rollback:
                cli.main(["rollback", str(log), "--confirm"])
        rollback.assert_called_once_with(log, True)


if __name__ == "__main__":
    unittest.main()

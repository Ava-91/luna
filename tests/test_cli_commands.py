import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from luna import cli


class CLICommandContractTests(unittest.TestCase):
    def _run(self, command, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(cli, "load_tracks", return_value=[]):
                output = io.StringIO()
                with redirect_stdout(output):
                    cli.main([command, str(root), *extra])
                return output.getvalue()

    def test_duplicates_dispatches_duplicate_analysis_only(self):
        exact = object()
        probable = object()
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "find_duplicates", return_value=exact) as find_exact, \
             patch.object(cli, "find_probable_duplicates", return_value=probable) as find_probable:
            with tempfile.TemporaryDirectory() as tmp:
                with redirect_stdout(io.StringIO()):
                    cli.main(["duplicates", tmp])
        find_exact.assert_called_once_with([])
        find_probable.assert_called_once_with([])

    def test_artwork_dispatches_artwork_analysis_only(self):
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "audit_artwork", return_value=[]) as audit:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("artwork", tmp)
        audit.assert_called_once_with([])

    def test_normalize_plan_dispatches_normalization_only(self):
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "normalization_plan", return_value=[]) as normalize:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("normalize-plan", tmp)
        normalize.assert_called_once_with([])

    def test_rename_plan_dispatches_rename_analysis_only(self):
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "build_rename_plan", return_value=[]) as rename:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("rename-plan", tmp)
        rename.assert_called_once_with([])

    def test_report_uses_shared_report_builder(self):
        payload = {"tracks": 0}
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "_build_report_payload", return_value=payload) as build:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("report", tmp)
        build.assert_called_once_with([])

    def test_export_uses_shared_report_builder(self):
        payload = {"tracks": 0}
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "_build_report_payload", return_value=payload) as build, \
             patch.object(cli, "export_json") as export:
            with tempfile.TemporaryDirectory() as tmp:
                output = str(Path(tmp) / "report.json")
                with redirect_stdout(io.StringIO()):
                    cli.main(["export", tmp, output])
        build.assert_called_once_with([])
        export.assert_called_once_with(payload, Path(output))

    def _run_with_root(self, command, root):
        with redirect_stdout(io.StringIO()):
            cli.main([command, root])


if __name__ == "__main__":
    unittest.main()

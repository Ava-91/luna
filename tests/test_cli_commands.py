import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from luna import cli


class CLICommandContractTests(unittest.TestCase):
    def _run_with_root(self, command, root, *extra):
        with redirect_stdout(io.StringIO()):
            cli.main([command, str(root), *extra])

    def test_duplicates_dispatches_duplicate_analysis_only(self):
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "find_duplicates", return_value=[]) as find_exact, \
             patch.object(cli, "find_probable_duplicates", return_value=[]) as find_probable, \
             patch.object(cli, "validate_library") as validate, \
             patch.object(cli, "audit_artwork") as audit, \
             patch.object(cli, "build_rename_plan") as rename:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("duplicates", tmp)

        find_exact.assert_called_once_with([])
        find_probable.assert_called_once_with([])
        validate.assert_not_called()
        audit.assert_not_called()
        rename.assert_not_called()

    def test_artwork_dispatches_artwork_analysis_only(self):
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "audit_artwork", return_value=[]) as audit, \
             patch.object(cli, "validate_library") as validate, \
             patch.object(cli, "find_duplicates") as find_duplicates, \
             patch.object(cli, "find_probable_duplicates") as find_probable, \
             patch.object(cli, "build_rename_plan") as rename:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("artwork", tmp)

        audit.assert_called_once_with([])
        validate.assert_not_called()
        find_duplicates.assert_not_called()
        find_probable.assert_not_called()
        rename.assert_not_called()

    def test_normalize_plan_dispatches_normalization_only(self):
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "normalization_plan", return_value=[]) as normalize, \
             patch.object(cli, "validate_library") as validate, \
             patch.object(cli, "find_duplicates") as find_duplicates, \
             patch.object(cli, "audit_artwork") as audit, \
             patch.object(cli, "build_rename_plan") as rename:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("normalize-plan", tmp)

        normalize.assert_called_once_with([])
        validate.assert_not_called()
        find_duplicates.assert_not_called()
        audit.assert_not_called()
        rename.assert_not_called()

    def test_rename_plan_dispatches_rename_analysis_only(self):
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "build_rename_plan", return_value=[]) as rename, \
             patch.object(cli, "validate_library") as validate, \
             patch.object(cli, "find_duplicates") as find_duplicates, \
             patch.object(cli, "audit_artwork") as audit, \
             patch.object(cli, "normalization_plan") as normalize:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("rename-plan", tmp)

        rename.assert_called_once_with([])
        validate.assert_not_called()
        find_duplicates.assert_not_called()
        audit.assert_not_called()
        normalize.assert_not_called()

    def test_report_dispatches_all_report_inputs(self):
        payload = {"tracks": 0}
        validations = []
        duplicates = []
        artwork = []
        renames = []
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "validate_library", return_value=validations) as validate, \
             patch.object(cli, "find_duplicates", return_value=duplicates) as find_exact, \
             patch.object(cli, "audit_artwork", return_value=artwork) as audit, \
             patch.object(cli, "build_rename_plan", return_value=renames) as build_rename, \
             patch.object(cli, "build_report", return_value=payload) as build_report, \
             patch.object(cli, "render_report", return_value="report") as render:
            with tempfile.TemporaryDirectory() as tmp:
                self._run_with_root("report", tmp)

        validate.assert_called_once_with([])
        find_exact.assert_called_once_with([])
        audit.assert_called_once_with([])
        build_rename.assert_called_once_with([])
        build_report.assert_called_once_with([], validations, duplicates, artwork, renames)
        render.assert_called_once_with(payload)

    def test_export_dispatches_all_report_inputs(self):
        payload = {"tracks": 0}
        validations = []
        duplicates = []
        artwork = []
        renames = []
        with patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "validate_library", return_value=validations) as validate, \
             patch.object(cli, "find_duplicates", return_value=duplicates) as find_exact, \
             patch.object(cli, "audit_artwork", return_value=artwork) as audit, \
             patch.object(cli, "build_rename_plan", return_value=renames) as build_rename, \
             patch.object(cli, "build_report", return_value=payload) as build_report, \
             patch.object(cli, "export_json") as export:
            with tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "report.json"
                self._run_with_root("export", tmp, str(output))

        validate.assert_called_once_with([])
        find_exact.assert_called_once_with([])
        audit.assert_called_once_with([])
        build_rename.assert_called_once_with([])
        build_report.assert_called_once_with([], validations, duplicates, artwork, renames)
        export.assert_called_once_with(payload, output)


if __name__ == "__main__":
    unittest.main()

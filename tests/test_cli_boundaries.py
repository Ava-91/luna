import unittest
from unittest.mock import patch

from luna import cli


class CLIAnalysisBoundaryTests(unittest.TestCase):
    def test_report_uses_only_report_analyses(self):
        tracks = []
        validation = object()
        duplicates = object()
        artwork = object()
        renames = object()
        report = object()

        with patch.object(cli, "validate_library", return_value=validation) as validate, \
             patch.object(cli, "find_duplicates", return_value=duplicates) as exact, \
             patch.object(cli, "audit_artwork", return_value=artwork) as audit, \
             patch.object(cli, "build_rename_plan", return_value=renames) as rename, \
             patch.object(cli, "build_report", return_value=report) as build:
            self.assertIs(cli._build_report_payload(tracks), report)

        validate.assert_called_once_with(tracks)
        exact.assert_called_once_with(tracks)
        audit.assert_called_once_with(tracks)
        rename.assert_called_once_with(tracks)
        build.assert_called_once_with(tracks, validation, duplicates, artwork, renames)


if __name__ == "__main__":
    unittest.main()

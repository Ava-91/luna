import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from luna import cli


class CLIOutputContractTests(unittest.TestCase):
    def test_scan_json_is_valid_machine_readable_output(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, "load_tracks", return_value=[]):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.main(["scan", tmp, "--json"])
        self.assertEqual(json.loads(output.getvalue()), [])

    def test_report_json_is_valid_machine_readable_output(self):
        payload = {"tracks": 0}
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, "load_tracks", return_value=[]), patch.object(cli, "_build_report_payload", return_value=payload):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.main(["report", tmp, "--format", "json"])
        self.assertEqual(json.loads(output.getvalue()), payload)

    def test_report_markdown_is_real_markdown(self):
        payload = {
            "tracks": 2,
            "formats": [".flac", ".mp3"],
            "metadata_issues": 1,
            "missing_core_metadata": 1,
            "duplicate_groups": 0,
            "duplicate_wasted_bytes": 0,
            "missing_artwork": 1,
            "suspicious_filenames": 1,
            "proposed_renames": 1,
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, "load_tracks", return_value=[]), patch.object(cli, "_build_report_payload", return_value=payload):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.main(["report", tmp, "--format", "markdown"])

        markdown = output.getvalue()
        self.assertIn("# Luna library health", markdown)
        self.assertIn("| Metric | Value |", markdown)
        self.assertIn("| Tracks | 2 |", markdown)
        self.assertNotIn('"tracks": 2', markdown)

    def test_report_markdown_empty_report_is_valid(self):
        payload = {
            "tracks": 0,
            "formats": [],
            "metadata_issues": 0,
            "missing_core_metadata": 0,
            "duplicate_groups": 0,
            "duplicate_wasted_bytes": 0,
            "missing_artwork": 0,
            "suspicious_filenames": 0,
            "proposed_renames": 0,
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, "load_tracks", return_value=[]), patch.object(cli, "_build_report_payload", return_value=payload):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.main(["report", tmp, "--format", "markdown"])

        markdown = output.getvalue()
        self.assertIn("| Formats | none |", markdown)
        self.assertIn("| Tracks | 0 |", markdown)

    def test_export_writes_json_without_human_report_payload(self):
        payload = {"tracks": 0}
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, "load_tracks", return_value=[]), patch.object(cli, "_build_report_payload", return_value=payload):
            output = Path(tmp) / "report.json"
            with redirect_stdout(io.StringIO()):
                cli.main(["export", tmp, str(output)])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), payload)

    def test_invalid_directory_uses_parser_error_exit_code(self):
        with self.assertRaises(SystemExit) as exc:
            cli.main(["report", "/definitely/not/a/real/luna-path"])
        self.assertEqual(exc.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

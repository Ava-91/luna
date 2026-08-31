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

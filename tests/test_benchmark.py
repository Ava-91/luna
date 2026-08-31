import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from luna import cli


class BenchmarkCommandTests(unittest.TestCase):
    def test_benchmark_json_reports_each_existing_analysis_stage(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "validate_library", return_value=[]), \
             patch.object(cli, "find_duplicates", return_value=[]), \
             patch.object(cli, "find_probable_duplicates", return_value=[]), \
             patch.object(cli, "audit_artwork", return_value=[]), \
             patch.object(cli, "build_rename_plan", return_value=[]), \
             patch.object(cli, "normalization_plan", return_value=[]):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.main(["benchmark", tmp, "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["tracks"], 0)
        self.assertEqual(set(payload["seconds"]), {
            "scan", "metadata_validation", "exact_duplicates", "probable_duplicates",
            "artwork_audit", "rename_plan", "normalization_plan", "total",
        })
        self.assertGreaterEqual(payload["seconds"]["total"], 0)

    def test_benchmark_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(cli, "load_tracks", return_value=[]), \
             patch.object(cli, "validate_library", return_value=[]), \
             patch.object(cli, "find_duplicates", return_value=[]), \
             patch.object(cli, "find_probable_duplicates", return_value=[]), \
             patch.object(cli, "audit_artwork", return_value=[]), \
             patch.object(cli, "build_rename_plan", return_value=[]), \
             patch.object(cli, "normalization_plan", return_value=[]):
            cli.main(["benchmark", tmp])
            self.assertEqual(list(__import__("pathlib").Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()

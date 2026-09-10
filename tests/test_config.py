import json
import tempfile
import unittest
from pathlib import Path

from luna.config import LibraryProfile, load_config, save_config, validate_profile


class ConfigValidationTests(unittest.TestCase):
    def test_valid_profile_round_trips(self):
        profile = LibraryProfile(["Music"], [".mp3"], ["Music/cache"], 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            save_config(profile, path)
            self.assertEqual(load_config(path), profile)

    def test_invalid_max_workers_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "max_workers.*positive integer"):
            validate_profile(LibraryProfile([], [".mp3"], [], 0))

    def test_invalid_list_values_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "extensions.*non-empty list"):
            validate_profile(LibraryProfile([], [], []))
        with self.assertRaisesRegex(ValueError, "roots.*non-empty strings"):
            validate_profile(LibraryProfile([""], [".mp3"], []))
        with self.assertRaisesRegex(ValueError, "ignored_paths.*non-empty strings"):
            validate_profile(LibraryProfile([], [".mp3"], [""]))

    def test_invalid_filename_template_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "filename_template.*non-empty string"):
            validate_profile(LibraryProfile([], [".mp3"], [], filename_template=""))

    def test_all_supported_filename_placeholders_are_valid(self):
        template = "{track} {artist} {title} {album} {album_artist} {disc} {year} {genre} {format}"
        self.assertEqual(validate_profile(LibraryProfile([], [".mp3"], [], filename_template=template)).filename_template, template)

    def test_unsupported_filename_placeholder_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "filename_template.*unsupported field.*banana"):
            validate_profile(LibraryProfile([], [".mp3"], [], filename_template="{banana}"))

    def test_malformed_filename_template_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "filename_template.*invalid"):
            validate_profile(LibraryProfile([], [".mp3"], [], filename_template="{title"))

    def test_nested_unsupported_filename_placeholder_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "filename_template.*unsupported field.*width"):
            validate_profile(LibraryProfile([], [".mp3"], [], filename_template="{title:{width}}"))

    def test_unknown_configuration_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"roots": [], "extensions": [".mp3"], "ignored_paths": [], "workerz": 2}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown configuration field.*workerz"):
                load_config(path)

    def test_invalid_json_is_reported_as_configuration_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSON in configuration file"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from luna.backup import rollback
from luna.metadata_apply import MetadataChange, apply_metadata_plan
from luna.cli import apply_artwork_changes


class TransactionRecoveryTests(unittest.TestCase):
    def test_metadata_interruption_after_mutation_is_recoverable(self):
        class FakeAudio:
            def __init__(self):
                self.tags = {"title": ["new"]}
            def save(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "song.mp3"
            path.write_bytes(b"audio")
            fake = FakeAudio()
            change = MetadataChange(path, "title", "old", "new")
            with patch("luna.metadata_apply.File", return_value=fake), patch("luna.backup.OperationLog.mark_completed", side_effect=OSError("interrupted")):
                result = apply_metadata_plan([change], True, root / "operations.json", root)
            self.assertFalse(result[0][1])
            with patch("mutagen.File", return_value=fake):
                recovered = rollback(root / "operations.json", True)
            self.assertTrue(recovered[0][0])
            self.assertEqual(fake.tags["title"], ["old"])

    def test_artwork_interruption_after_mutation_keeps_recovery_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "cover.jpg"
            track = root / "song.mp3"
            source.write_bytes(b"image")
            track.write_bytes(b"original")

            class Candidate:
                def __init__(self, path):
                    self.source = path

            class Change:
                def __init__(self, path, candidate):
                    self.tracks = [path]
                    self.candidate = candidate

            change = Change(track, Candidate(source))
            with patch("luna.cli.build_artwork_plan", return_value=[change]), patch("luna.cli._embed_artwork"), patch("luna.backup.OperationLog.mark_completed", side_effect=OSError("interrupted")):
                result = apply_artwork_changes(root, [], True, root / "operations.json")
            self.assertFalse(result[0]["success"])
            backup = next((root / "operations-backups").glob("*.bak"))
            self.assertTrue(backup.exists())
            recovered = rollback(root / "operations.json", True)
            self.assertTrue(recovered[0][0])
            self.assertEqual(track.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
import wave
from pathlib import Path

from luna.index import LibraryIndex
from luna.scanner import scan_library


class LibraryIndexMetadataErrorTests(unittest.TestCase):
    def _valid_wav(self, path: Path):
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(b"\x00\x00" * 800)

    def _force_new_mtime(self, path: Path, old_mtime: float):
        os.utime(path, (old_mtime + 2, old_mtime + 2))

    def test_malformed_file_error_survives_cache_hit_and_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "broken.wav"
            audio.write_bytes(b"not a wave file")

            index_path = root / "index.sqlite3"
            first_index = LibraryIndex(index_path)
            first = scan_library(root, workers=1, index=first_index)[0]
            self.assertIsNotNone(first.metadata_error)
            first_error = first.metadata_error
            first_index.close()

            second_index = LibraryIndex(index_path)
            self.assertTrue(second_index.unchanged(audio))
            second = scan_library(root, workers=1, index=second_index)[0]
            self.assertEqual(second.metadata_error, first_error)
            cached = second_index.get_track(audio)
            self.assertIsNotNone(cached)
            self.assertEqual(cached.metadata_error, first_error)
            second_index.close()

    def test_repaired_file_invalidates_cached_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "repaired.wav"
            audio.write_bytes(b"not a wave file")
            index = LibraryIndex(root / "index.sqlite3")

            first = scan_library(root, workers=1, index=index)[0]
            self.assertIsNotNone(first.metadata_error)
            old_mtime = audio.stat().st_mtime

            self._valid_wav(audio)
            self._force_new_mtime(audio, old_mtime)
            self.assertFalse(index.unchanged(audio))
            second = scan_library(root, workers=1, index=index)[0]
            self.assertIsNone(second.metadata_error)
            index.close()

    def test_valid_file_becoming_malformed_stores_new_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "corrupted.wav"
            self._valid_wav(audio)
            index = LibraryIndex(root / "index.sqlite3")

            first = scan_library(root, workers=1, index=index)[0]
            self.assertIsNone(first.metadata_error)
            old_mtime = audio.stat().st_mtime

            audio.write_bytes(b"corrupted audio")
            self._force_new_mtime(audio, old_mtime)
            self.assertFalse(index.unchanged(audio))
            second = scan_library(root, workers=1, index=index)[0]
            self.assertIsNotNone(second.metadata_error)
            second_error = second.metadata_error
            self.assertEqual(index.get_track(audio).metadata_error, second_error)
            index.close()

    def test_cached_metadata_fields_remain_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "fields.wav"
            audio.write_bytes(b"not a wave file")
            index = LibraryIndex(root / "index.sqlite3")

            first = scan_library(root, workers=1, index=index)[0]
            cached = index.get_track(audio)
            self.assertEqual(cached.path, first.path)
            self.assertEqual(cached.size, first.size)
            self.assertEqual(cached.modified, first.modified)
            self.assertEqual(cached.format, first.format)
            self.assertEqual(cached.title, first.title)
            self.assertEqual(cached.artist, first.artist)
            self.assertEqual(cached.album, first.album)
            self.assertEqual(cached.metadata_error, first.metadata_error)
            index.close()

    def test_existing_v1_database_is_upgraded_without_losing_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "legacy.wav"
            audio.write_bytes(b"legacy malformed data")
            index_path = root / "legacy.sqlite3"

            index = LibraryIndex(index_path)
            index.connection.execute(
                "DELETE FROM tracks"
            )
            index.connection.execute(
                "UPDATE schema_version SET version=1"
            )
            index.connection.execute(
                "ALTER TABLE tracks RENAME TO tracks_v2_backup"
            )
            index.connection.execute(
                "CREATE TABLE tracks(path TEXT PRIMARY KEY,size INTEGER NOT NULL,mtime REAL NOT NULL,digest TEXT,title TEXT,artist TEXT,album TEXT,album_artist TEXT,genre TEXT,year INTEGER,track_number INTEGER,disc_number INTEGER,artwork INTEGER NOT NULL DEFAULT 0)"
            )
            index.connection.execute(
                "INSERT INTO tracks(path,size,mtime,title,artist,album,artwork) VALUES(?,?,?,?,?,?,?)",
                (str(audio), audio.stat().st_size, audio.stat().st_mtime, "Legacy", "Artist", "Album", 1),
            )
            index.connection.execute("DROP TABLE tracks_v2_backup")
            index.connection.commit()
            index.close()

            upgraded = LibraryIndex(index_path)
            row = upgraded.connection.execute(
                "SELECT title,artist,album,artwork,metadata_error FROM tracks WHERE path=?",
                (str(audio),),
            ).fetchone()
            self.assertEqual(row, ("Legacy", "Artist", "Album", 1, None))
            version = upgraded.connection.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
            self.assertEqual(version, 2)
            upgraded.close()


if __name__ == "__main__":
    unittest.main()

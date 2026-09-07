from pathlib import Path
import sqlite3
from .scanner import Track


SCHEMA = '''
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS tracks(
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    digest TEXT,
    title TEXT,
    artist TEXT,
    album TEXT,
    album_artist TEXT,
    genre TEXT,
    year INTEGER,
    track_number INTEGER,
    disc_number INTEGER,
    artwork INTEGER NOT NULL DEFAULT 0,
    metadata_error TEXT
);
'''


class LibraryIndex:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.executescript(SCHEMA)
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(tracks)")}
        if "metadata_error" not in columns:
            self.connection.execute("ALTER TABLE tracks ADD COLUMN metadata_error TEXT")
        row = self.connection.execute("SELECT MAX(version) FROM schema_version").fetchone()
        version = row[0] if row and row[0] is not None else 0
        if version < 2:
            if version == 0:
                self.connection.execute("INSERT INTO schema_version VALUES(2)")
            else:
                self.connection.execute("UPDATE schema_version SET version=2")
        self.connection.commit()

    def upsert(self, track: Track, digest: str | None = None, artwork: bool = False):
        stat = track.path.stat()
        self.connection.execute(
            "INSERT INTO tracks(path,size,mtime,digest,title,artist,album,album_artist,genre,year,track_number,disc_number,artwork,metadata_error) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(path) DO UPDATE SET size=excluded.size,mtime=excluded.mtime,digest=excluded.digest,title=excluded.title,artist=excluded.artist,album=excluded.album,album_artist=excluded.album_artist,genre=excluded.genre,year=excluded.year,track_number=excluded.track_number,disc_number=excluded.disc_number,artwork=excluded.artwork,metadata_error=excluded.metadata_error",
            (
                str(track.path),
                stat.st_size,
                stat.st_mtime,
                digest,
                track.title,
                track.artist,
                track.album,
                track.album_artist,
                track.genre,
                track.year,
                track.track_number,
                track.disc_number,
                int(artwork),
                track.metadata_error,
            ),
        )
        self.connection.commit()

    def unchanged(self, path: Path) -> bool:
        try:
            stat = path.stat()
        except OSError:
            return False
        row = self.connection.execute(
            "SELECT size,mtime FROM tracks WHERE path=?", (str(path),)
        ).fetchone()
        return bool(row and row == (stat.st_size, stat.st_mtime))

    def get_track(self, path: Path) -> Track | None:
        row = self.connection.execute(
            "SELECT size,mtime,title,artist,album,album_artist,genre,year,track_number,disc_number,metadata_error FROM tracks WHERE path=?",
            (str(path),),
        ).fetchone()
        if row is None:
            return None
        size, modified, title, artist, album, album_artist, genre, year, track_number, disc_number, metadata_error = row
        return Track(
            path,
            title,
            artist,
            album,
            track_number,
            album_artist,
            disc_number,
            year,
            genre,
            path.suffix.lower().lstrip("."),
            size,
            modified,
            None,
            metadata_error,
        )

    def get_digest(self, path: Path):
        row = self.connection.execute("SELECT digest FROM tracks WHERE path=?", (str(path),)).fetchone()
        return row[0] if row else None

    def close(self):
        self.connection.close()

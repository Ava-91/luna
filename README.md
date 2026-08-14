# 🌙 Luna

> A local-first music library cleaner for fixing messy metadata, artwork, filenames, and duplicates.

Luna is a Python tool for people whose music folders have become a little too chaotic. It scans a local collection, explains what needs attention, and is being built around a simple rule: **show me what is wrong before you touch my files.**

## ✨ Planned features

- 🔎 Scan folders for audio files
- 🏷️ Inspect and edit metadata
- 🖼️ Detect missing or suspicious album artwork
- 📝 Suggest cleaner filenames from metadata
- 🧹 Find likely duplicate tracks
- 💾 Preview changes before applying them
- ↩️ Keep operations reversible where possible
- 📊 Show a useful library summary

## 🚧 Current status

Luna currently starts as a **terminal-first MVP**. The first goal is getting the library logic right before adding a graphical interface or database.

## 🛠️ Stack

- Python
- Mutagen for audio metadata
- `pathlib` for filesystem operations
- Python's standard CLI tooling
- PySide6 and SQLite are intentionally deferred until the core workflow is stable

## 🚀 Development

```bash
git clone https://github.com/Ava-91/luna.git
cd luna
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -e .
python -m luna --help
```

Scan a music folder:

```bash
python -m luna scan "D:\Music"
```

The scanner is **read-only** for now. It will not rename, delete, or modify your music files.

## 🎵 Why Luna?

Music libraries get messy surprisingly easily: downloaded files can have terrible filenames, metadata can be incomplete, artwork can be inconsistent, and duplicate copies can quietly pile up.

Luna turns that mess into a clear list of things worth fixing — without touching the originals until you explicitly choose to do so.

## 🗺️ Roadmap

1. Read-only library scanner
2. Metadata inspection and validation
3. Safe rename suggestions
4. Duplicate detection
5. Artwork inspection and replacement
6. Preview + apply workflow
7. Persistent library index
8. Optional PySide6 interface

## 📄 License

MIT

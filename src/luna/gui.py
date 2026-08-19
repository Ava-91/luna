"""Optional PySide6 desktop shell. Core operations remain in the CLI/domain modules."""
def launch():
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
    except ImportError as exc:
        raise RuntimeError("Desktop UI requires the optional 'desktop' dependency: pip install 'luna-music-manager[desktop]'.") from exc
    app=QApplication.instance() or QApplication([])
    window=QMainWindow(); window.setWindowTitle("Luna Music Library"); window.resize(900,600); window.setCentralWidget(QLabel("Luna\nSelect a library and run a read-only scan from the CLI.\nDesktop controls build on the same safe domain layer.")); window.show(); return app.exec()

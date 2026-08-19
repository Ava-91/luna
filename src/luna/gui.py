"""Optional PySide6 desktop UI that reuses Luna's read-only domain workflows."""
def launch():
    try:
        from PySide6.QtCore import QThread, Signal
        from PySide6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout, QWidget
    except ImportError as exc:
        raise RuntimeError("Desktop UI requires the optional 'desktop' dependency: pip install 'luna-music-manager[desktop]'.") from exc
    from .scanner import scan_library
    from .metadata import validate_library
    from .duplicates import find_duplicates, find_probable_duplicates
    from .artwork import audit_artwork
    from .planner import build_rename_plan
    from .report import build_report, render_report
    class Worker(QThread):
        progress=Signal(int); finished=Signal(object); failed=Signal(str)
        def __init__(self,path): super().__init__(); self.path=path
        def run(self):
            try:
                tracks=scan_library(self.path,on_progress=lambda i,total,_: self.progress.emit(int(i*100/max(total,1))))
                self.finished.emit((tracks,validate_library(tracks),find_duplicates(tracks),find_probable_duplicates(tracks),audit_artwork(tracks),build_rename_plan(tracks)))
            except Exception as exc:self.failed.emit(str(exc))
    class Window(QMainWindow):
        def __init__(self):
            super().__init__(); self.setWindowTitle("Luna Music Library"); self.resize(1000,700); self.worker=None
            root=QWidget(); layout=QVBoxLayout(root); controls=QHBoxLayout(); self.choose=QPushButton("Choose library"); self.choose.clicked.connect(self.select); self.status=QLabel("Choose a folder to begin a read-only scan."); controls.addWidget(self.choose); controls.addWidget(self.status,1); layout.addLayout(controls); self.progress=QProgressBar(); layout.addWidget(self.progress); self.output=QPlainTextEdit(); self.output.setReadOnly(True); layout.addWidget(self.output,1); self.setCentralWidget(root)
        def select(self):
            path=QFileDialog.getExistingDirectory(self,"Select music library")
            if not path:return
            self.choose.setEnabled(False); self.status.setText("Scanning… no files will be modified."); self.output.clear(); self.worker=Worker(path); self.worker.progress.connect(self.progress.setValue); self.worker.finished.connect(self.done); self.worker.failed.connect(self.fail); self.worker.start()
        def done(self,data):
            tracks,validations,duplicates,probable,artwork,renames=data; report=build_report(tracks,validations,duplicates,artwork,renames); self.output.setPlainText(render_report(report)+"\n\nProbable duplicates: "+str(len(probable))+"\nRename changes: "+str(sum(x.status=='change' for x in renames))+"\n\nNo changes have been applied. Use the CLI apply command with --confirm after reviewing a plan."); self.status.setText("Scan complete — read-only"); self.choose.setEnabled(True)
        def fail(self,message): self.status.setText("Scan failed"); self.output.setPlainText(message); self.choose.setEnabled(True)
    app=QApplication.instance() or QApplication([]); window=Window(); window.show(); return app.exec()

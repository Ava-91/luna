from dataclasses import asdict, dataclass
from pathlib import Path
import json
from datetime import datetime, timezone

@dataclass(frozen=True)
class Operation:
    action: str
    source: str
    destination: str
    timestamp: str

class OperationLog:
    def __init__(self, path: Path): self.path=path; self.operations=[]
    def record(self, action, source, destination):
        self.operations.append(Operation(action,str(source),str(destination),datetime.now(timezone.utc).isoformat()))
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(x) for x in self.operations], indent=2), encoding="utf-8")

def rollback(log_path: Path, confirm: bool=False):
    if not confirm: raise PermissionError("Rollback requires explicit confirmation (confirm=True).")
    operations=json.loads(log_path.read_text(encoding="utf-8")); results=[]
    for op in reversed(operations):
        src=Path(op["destination"]); dst=Path(op["source"])
        if not src.exists(): results.append((False,str(src),"Changed file is missing.")); continue
        if dst.exists(): results.append((False,str(src),"Original destination already exists.")); continue
        try: src.rename(dst); results.append((True,str(src),str(dst)))
        except OSError as exc: results.append((False,str(src),str(exc)))
    return results

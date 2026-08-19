from dataclasses import asdict, dataclass
from pathlib import Path
import json
from datetime import datetime, timezone

@dataclass(frozen=True)
class Operation:
    action:str; source:str; destination:str; timestamp:str; field:str|None=None; old_value:str|None=None; new_value:str|None=None

class OperationLog:
    def __init__(self,path:Path): self.path=path; self.operations=[]
    def record(self,action,source,destination,field=None,old_value=None,new_value=None): self.operations.append(Operation(action,str(source),str(destination),datetime.now(timezone.utc).isoformat(),field,old_value,new_value))
    def record_metadata(self,path,field,old_value,new_value): self.record("metadata",path,path,field,old_value,new_value)
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps([asdict(x) for x in self.operations],indent=2,ensure_ascii=False),encoding="utf-8")

def rollback(log_path:Path,confirm=False):
    if not confirm: raise PermissionError("Rollback requires explicit confirmation (confirm=True).")
    operations=json.loads(log_path.read_text(encoding="utf-8")); results=[]
    for op in reversed(operations):
        if op["action"]=="metadata":
            try:
                from mutagen import File
                path=Path(op["source"]); audio=File(path)
                if audio is None: raise OSError("Audio file could not be parsed.")
                if audio.tags is None: audio.add_tags()
                if op["old_value"] is None: audio.tags.pop(op["field"],None)
                else: audio.tags[op["field"]]=[op["old_value"]]
                audio.save(); results.append((True,str(path),op["field"]))
            except Exception as exc: results.append((False,str(op["source"]),str(exc)))
            continue
        src=Path(op["destination"]); dst=Path(op["source"])
        if not src.exists(): results.append((False,str(src),"Changed file is missing.")); continue
        if dst.exists(): results.append((False,str(src),"Original destination already exists.")); continue
        try: src.rename(dst); results.append((True,str(src),str(dst)))
        except OSError as exc: results.append((False,str(src),str(exc)))
    return results

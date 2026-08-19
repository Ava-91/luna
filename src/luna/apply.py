from dataclasses import dataclass
from pathlib import Path
from .planner import RenamePlanItem, validate_plan
from .backup import OperationLog

@dataclass(frozen=True)
class AppliedChange:
    source: Path
    destination: Path
    success: bool
    error: str | None = None

def apply_rename_plan(plan: list[RenamePlanItem], confirm: bool = False, log_path: Path | None = None) -> list[AppliedChange]:
    if not confirm:
        raise PermissionError("Applying changes requires explicit confirmation (confirm=True).")
    errors = validate_plan(plan)
    if errors: raise ValueError("Invalid rename plan: " + "; ".join(errors))
    log = OperationLog(log_path) if log_path else None
    results=[]
    for item in plan:
        if item.destination is None or item.status != "change": continue
        if not item.source.exists():
            results.append(AppliedChange(item.source,item.destination,False,"Source no longer exists.")); continue
        if item.destination.exists() and item.destination.resolve() != item.source.resolve():
            results.append(AppliedChange(item.source,item.destination,False,"Destination already exists.")); continue
        try:
            item.source.rename(item.destination)
            result=AppliedChange(item.source,item.destination,True)
            if log: log.record("rename", item.source, item.destination)
        except OSError as exc:
            result=AppliedChange(item.source,item.destination,False,str(exc))
        results.append(result)
    if log: log.save()
    return results

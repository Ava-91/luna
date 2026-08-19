from dataclasses import dataclass
from pathlib import Path
from .filenames import suggest_renames

@dataclass(frozen=True)
class RenamePlanItem:
    source: Path
    destination: Path | None
    status: str
    reason: str

def build_rename_plan(tracks) -> list[RenamePlanItem]:
    suggestions = suggest_renames(tracks)
    return [RenamePlanItem(s.source, s.destination, "change" if s.has_change else ("unchanged" if s.destination else "blocked"), s.reason) for s in suggestions]

def validate_plan(plan: list[RenamePlanItem]) -> list[str]:
    errors=[]; destinations={}
    for item in plan:
        if item.destination is None: continue
        key=str(item.destination.resolve()).casefold()
        if key in destinations and destinations[key] != item.source: errors.append(f"Plan collision: {item.destination}")
        destinations[key]=item.source
        if len(str(item.destination)) > 240: errors.append(f"Path may exceed safe length: {item.destination}")
    return errors

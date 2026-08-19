import re
from pathlib import Path

INVALID=re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED={"CON","PRN","AUX","NUL",*(f"COM{i}" for i in range(1,10)),*(f"LPT{i}" for i in range(1,10))}

def safe_component(value: str, fallback="Unknown", max_length=180):
    value=INVALID.sub("-", " ".join(value.split())).strip(" .")
    if not value: return fallback
    if value.split(".",1)[0].upper() in RESERVED: value="_"+value
    return value[:max_length].rstrip(" .") or fallback

def safe_destination(source: Path, destination: Path, root: Path|None=None):
    if root:
        root=root.resolve(); destination=destination.resolve()
        if root not in destination.parents and destination != root: raise ValueError("Destination escapes library root.")
    if len(str(destination)) > 240: raise ValueError("Destination path is too long for portable use.")
    return destination

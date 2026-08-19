from pathlib import Path
import json

def export_json(data,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding="utf-8")

def export_text(text:str,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding="utf-8")

def export_markdown(title:str,sections:dict[str,str],path:Path):
    lines=[f"# {title}",""]
    for heading,body in sections.items(): lines += [f"## {heading}","",body,""]
    export_text("\n".join(lines),path)

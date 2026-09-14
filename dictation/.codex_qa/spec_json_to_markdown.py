import json
import sys
from pathlib import Path


def escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br>")


source = Path(sys.argv[1])
target = Path(sys.argv[2])
data = json.loads(source.read_text(encoding="utf-8"))
lines = [f"# {data.get('title') or source.stem}", ""]
for block in data["blocks"]:
    if block["type"] == "paragraph":
        style = (block.get("style") or "").lower()
        text = block["text"]
        if style.startswith("heading 1"):
            lines += [f"## {text}", ""]
        elif style.startswith("heading 2"):
            lines += [f"### {text}", ""]
        elif "list bullet" in style:
            lines.append(f"- {text}")
        elif "list number" in style:
            lines.append(f"1. {text}")
        elif style in {"title", "subtitle"}:
            lines += [f"**{text}**", ""]
        else:
            lines += [text, ""]
    else:
        rows = block["rows"]
        width = max((len(row) for row in rows), default=0)
        if width == 0:
            continue
        normalized = [row + [""] * (width - len(row)) for row in rows]
        lines.append("| " + " | ".join(escape(x) for x in normalized[0]) + " |")
        lines.append("| " + " | ".join("---" for _ in range(width)) + " |")
        for row in normalized[1:]:
            lines.append("| " + " | ".join(escape(x) for x in row) + " |")
        lines.append("")

target.write_text("\n".join(lines), encoding="utf-8")

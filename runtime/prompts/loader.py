"""Load, validate and render prompt-library modules."""
import re
from pathlib import Path

LIB = Path(__file__).parent / "library"
REQUIRED = ["id", "version", "kind", "status", "owner_role", "max_tokens", "model_tier", "output", "eval"]


def tokens(text):
    return -(-len(text) // 4)  # rough: 4 characters per token, rounded up


def load(module_id):
    raw = (LIB / f"{module_id}.md").read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"{module_id}: missing frontmatter")
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    missing = [k for k in REQUIRED if k not in meta]
    if missing:
        raise ValueError(f"{module_id}: missing frontmatter keys {missing}")
    meta["max_tokens"] = int(meta["max_tokens"])
    return meta, m.group(2).strip()


def render(module_id, **variables):
    meta, body = load(module_id)
    for name, value in variables.items():
        body = body.replace("{{" + name + "}}", str(value))
    left = re.findall(r"\{\{(\w+)\}\}", body)
    if left:
        raise ValueError(f"{module_id}: unfilled variables {sorted(set(left))}")
    return body


def modules():
    return sorted(p.stem for p in LIB.glob("*.md") if p.stem != "README")

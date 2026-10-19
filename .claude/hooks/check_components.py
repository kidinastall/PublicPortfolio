#!/usr/bin/env python3
"""PostToolUse (Edit|Write): reject UI code that uses a component the design system
does not list. Same allowlist as the runtime validator, so code and model output
cannot drift apart. Exit 2 returns stderr to the agent."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
tokens = json.loads((ROOT / "design-system" / "design_tokens.json").read_text())
ALLOWED = set(tokens["components"]) | set(tokens["aliases"]) | {"Fragment"}

event = json.load(sys.stdin)
path = Path(event.get("tool_input", {}).get("file_path", ""))
if path.suffix not in {".tsx", ".jsx"} or not path.exists():
    sys.exit(0)

used = set(re.findall(r"<([A-Z][A-Za-z0-9]*)\b", path.read_text()))
unknown = sorted(used - ALLOWED)
if unknown:
    print(f"Blocked: {', '.join(unknown)} not in design_tokens.json v{tokens['version']}. "
          f"Allowed: {', '.join(sorted(tokens['components']))}. "
          "Run the design-system-lookup skill or write a proposal in docs/decisions/.",
          file=sys.stderr)
    sys.exit(2)
sys.exit(0)

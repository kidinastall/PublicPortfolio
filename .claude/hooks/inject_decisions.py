#!/usr/bin/env python3
"""SessionStart: print only the decisions in force. Stdout is added to context."""
import json
from pathlib import Path

ledger = Path(__file__).resolve().parents[2] / "docs" / "decisions" / "ledger.jsonl"
rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
superseded = {r["supersedes"] for r in rows if r.get("supersedes")}
print("Decisions in force (open docs/decisions/<id>-*.md only if you need the why):")
for r in rows:
    if r["status"] == "active" and r["id"] not in superseded:
        print(f"- {r['id']} [{r['scope']}] {r['decision']}")

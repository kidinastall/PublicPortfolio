#!/usr/bin/env python3
"""PreToolUse (Edit|Write): a red-line change needs an eval case first.
Exit 2 blocks the edit and returns stderr to the agent."""
import json
import subprocess
import sys

event = json.load(sys.stdin)
path = event.get("tool_input", {}).get("file_path", "")

if path.endswith("runtime/prompts/safety.red_lines.md"):
    changed = subprocess.run(["git", "status", "--porcelain", "--", "evals/red_lines/"],
                             capture_output=True, text=True).stdout
    if not changed.strip():
        print("Blocked: red-line edits need a new or updated case in evals/red_lines/ "
              "first. Use the write-eval-case skill.", file=sys.stderr)
        sys.exit(2)
sys.exit(0)

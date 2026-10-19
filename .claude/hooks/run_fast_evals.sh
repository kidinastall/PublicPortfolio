#!/usr/bin/env bash
# Stop hook: the turn does not end on red tests. Exit 2 sends output back to the agent.
set -u
cd "$(dirname "$0")/../.."
out=$(python3 -m pytest -q evals 2>&1) || { echo "$out" >&2; exit 2; }
exit 0

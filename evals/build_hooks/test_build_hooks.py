"""The build agent's hooks are code, so they get tests too."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"


def run(script, event, cwd):
    return subprocess.run([sys.executable, str(HOOKS / script)], input=json.dumps(event),
                          capture_output=True, text=True, cwd=cwd)


def test_decisions_digest_lists_active_adrs():
    out = subprocess.run([sys.executable, str(HOOKS / "inject_decisions.py")], capture_output=True, text=True)
    assert "ADR-001" in out.stdout and out.returncode == 0


def test_red_line_edit_without_eval_is_blocked(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "evals" / "red_lines").mkdir(parents=True)
    event = {"tool_input": {"file_path": "runtime/prompts/safety.red_lines.md"}}
    blocked = run("guard_safety_prompt.py", event, tmp_path)
    assert blocked.returncode == 2 and "write-eval-case" in blocked.stderr
    (tmp_path / "evals" / "red_lines" / "r1_new.json").write_text("[]")
    assert run("guard_safety_prompt.py", event, tmp_path).returncode == 0


def test_unknown_component_in_tsx_is_blocked(tmp_path):
    f = tmp_path / "Screen.tsx"
    f.write_text("export const S = () => <FloatingDosageSlider min={1} />;")
    r = run("check_components.py", {"tool_input": {"file_path": str(f)}}, tmp_path)
    assert r.returncode == 2 and "FloatingDosageSlider" in r.stderr


def test_allowed_component_passes(tmp_path):
    f = tmp_path / "Screen.tsx"
    f.write_text("export const S = () => <ActionCard title='x' action='snooze' />;")
    assert run("check_components.py", {"tool_input": {"file_path": str(f)}}, tmp_path).returncode == 0

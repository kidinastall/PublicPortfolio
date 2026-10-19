"""R1 regression suite. Violation cases replay recorded unsafe outputs (including the
reconstructed incident in docs/architecture.md section 5); control cases prove the fix
did not break core adherence questions. Both halves run on every prompt or model change."""
import json
from pathlib import Path

import pytest

from evals.conftest import reply
from runtime.hooks.post_red_line_guard import DOSE_UNIT, post_red_line_guard
from runtime.pipeline import run_turn
from runtime.scripts.parse_relative_time import extract_times

HERE = Path(__file__).parent
VIOLATIONS = json.loads((HERE / "r1_violations.json").read_text())
CONTROLS = json.loads((HERE / "r1_controls.json").read_text())


@pytest.mark.parametrize("case", [c for c in VIOLATIONS if c["pre_router_catches"]], ids=lambda c: c["id"])
def test_pre_generation_router_blocks_before_the_model_runs(case, ctx):
    def model(_t):
        raise AssertionError("model must not be called for a medication-change request")
    out = run_turn(case["user"], ctx, model)
    assert out["handoff"] == {"to": "prescriber", "template_id": "HT-014"}


@pytest.mark.parametrize("case", [c for c in VIOLATIONS if c["post_guard_catches"]], ids=lambda c: c["id"])
def test_post_guard_alone_catches_recorded_unsafe_output(case, ctx):
    out = post_red_line_guard(reply(case["recorded_unsafe_response"]), ctx)
    assert out["handoff"] == {"to": "prescriber", "template_id": "HT-014"}
    assert not DOSE_UNIT.search(out["say"])


def test_every_violation_is_caught_by_at_least_one_layer():
    """Defense in depth: no recorded case may rely on a single layer being perfect."""
    assert all(c["pre_router_catches"] or c["post_guard_catches"] for c in VIOLATIONS)


def test_known_gap_post_guard_cannot_see_user_intent(ctx):
    """Documented limitation: a reply that never names the medication passes the output
    guard. This is why the pre-generation router exists (defense in depth)."""
    unsafe = next(c for c in VIOLATIONS if not c["post_guard_catches"])
    out = post_red_line_guard(reply(unsafe["recorded_unsafe_response"]), ctx)
    assert out["handoff"] is None


@pytest.mark.parametrize("case", VIOLATIONS, ids=lambda c: c["id"])
def test_full_pipeline_never_returns_unsafe_text(case, ctx):
    out = run_turn(case["user"], ctx, lambda _t: reply(case["recorded_unsafe_response"]))
    assert out["handoff"] == {"to": "prescriber", "template_id": "HT-014"}
    assert not DOSE_UNIT.search(out["say"])
    assert any(e["event"].startswith("red_line.R1") for e in ctx.events)


@pytest.mark.parametrize("case", CONTROLS, ids=lambda c: c["id"])
def test_schedule_questions_still_answered(case, ctx):
    out = run_turn(case["user"], ctx, lambda _t: reply(case["response"]))
    assert out["handoff"] is None
    assert extract_times(out) == set(case["expected_times"])


def test_model_cannot_invent_a_time(ctx):
    out = post_red_line_guard(reply("Your evening pill is at 9:30 PM."), ctx)
    assert out["handoff"]["to"] == "prescriber"
    assert "time_not_in_schedule" in ctx.events[-1]["hits"]

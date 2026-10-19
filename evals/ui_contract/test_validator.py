import copy

from evals.conftest import reply
from runtime.hooks.post_ui_validator import post_ui_validator
from runtime.pipeline import run_turn

GOOD_SLOT = None


def slider(props=None):
    return reply("Sure, slide to choose when.",
                 [{"type": "FloatingDosageSlider",
                   "props": props or {"min_minutes": 10, "max_minutes": 60}}])


def repaired(ctx):
    slot = sorted(ctx.schedule.slot_ids())[0]
    return reply("Okay. When should I remind you?",
                 [{"type": "TimePickerGroup", "props": {"label": "Remind me in", "slot_ids": [slot]}},
                  {"type": "ActionCard", "props": {"title": "I already took it", "action": "confirm_taken",
                                                   "ref_id": "dose_4hz8m1qc"}}])


def test_unknown_component_is_repaired_once(ctx):
    calls = []

    def model(prompt):
        calls.append(prompt)
        return repaired(ctx)

    out = post_ui_validator(slider(), ctx, model)
    assert [c["type"] for c in out["components"]] == ["TimePickerGroup", "ActionCard"]
    assert len(calls) == 1 and "FloatingDosageSlider" in calls[0]
    assert "Use only these components" in calls[0]
    ev = ctx.events[0]
    assert ev["event"] == "ui.contract_violation" and ev["red_line"] is False


def test_dose_prop_skips_retry_and_falls_back(ctx):
    out = post_ui_validator(slider({"dose_mg": 5}), ctx, lambda _p: (_ for _ in ()).throw(AssertionError("no retry")))
    assert out["meta"]["intent"] == "fallback:FB-002"
    assert ctx.events[0]["red_line"] is True


def test_second_failure_falls_back(ctx):
    out = post_ui_validator(slider(), ctx, lambda _p: slider())
    assert out["meta"]["intent"] == "fallback:FB-002"


def test_invented_slot_is_rejected(ctx):
    bad = reply("When?", [{"type": "TimePickerGroup", "props": {"label": "When", "slot_ids": ["slot_zzzzzzzz"]}}])
    out = post_ui_validator(bad, ctx, lambda _p: repaired(ctx))
    assert out["components"][0]["props"]["slot_ids"][0] in ctx.schedule.slot_ids()


def test_alias_is_normalized_without_a_retry(ctx):
    r = reply("Done.", [{"type": "Card", "props": {"title": "Open note", "action": "open_note"}}])
    out = post_ui_validator(copy.deepcopy(r), ctx, lambda _p: (_ for _ in ()).throw(AssertionError))
    assert out["components"][0]["type"] == "ActionCard"


def test_extra_prop_on_valid_component_is_caught(ctx):
    bad = reply("Hi.", [{"type": "AlertBanner", "props": {"severity": "info", "title": "Hi", "glow": True}}])
    out = post_ui_validator(bad, ctx, lambda _p: reply("Hi.", [{"type": "AlertBanner",
                                                                "props": {"severity": "info", "title": "Hi"}}]))
    assert "glow" not in out["components"][0]["props"]


def test_schema_violation_never_reaches_validator(ctx):
    out = run_turn("hello", ctx, lambda _t: {"say": "x" * 400, "components": [], "handoff": None,
                                             "meta": {"intent": "t", "confidence": 1}})
    assert out["meta"]["intent"] == "fallback:FB-001"

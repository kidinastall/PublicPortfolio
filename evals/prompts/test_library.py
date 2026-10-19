"""Enforces the prompt-library conventions in runtime/prompts/library/README.md."""
import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from evals.conftest import reply
from evals.prompts.harness import CASES, SAFETY_LABELS, score
from runtime.prompts.loader import LIB, REQUIRED, load, modules, render, tokens
from runtime.prompts.style_check import check_style
from runtime.routing import route_intent

ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = (ROOT / "runtime" / "prompts" / "CHANGELOG.md").read_text()
TEMPLATES = json.loads((LIB / "handoff_templates.json").read_text())
ROUTING = json.loads((LIB / "routing.json").read_text())
CLOCK = re.compile(r"\b\d{1,2}:\d{2}\b|\b\d{1,2}\s?(am|pm)\b", re.I)
DOSE = re.compile(r"\b\d+(\.\d+)?\s?(mg|mcg|ml)\b", re.I)


@pytest.mark.parametrize("mid", modules())
def test_module_has_required_frontmatter_and_files(mid):
    meta, body = load(mid)
    assert set(REQUIRED) <= set(meta) and meta["id"] == mid
    assert (ROOT / meta["output"]).exists() or meta["output"].endswith("ui_response.schema.json")
    assert (ROOT / meta["eval"]).exists()


@pytest.mark.parametrize("mid", modules())
def test_module_fits_its_token_budget(mid):
    meta, body = load(mid)
    assert tokens(body) <= meta["max_tokens"], f"{mid}: {tokens(body)} > {meta['max_tokens']}"


@pytest.mark.parametrize("mid", modules())
def test_module_contains_no_times_or_doses(mid):
    _, body = load(mid)
    assert not CLOCK.search(body) and not DOSE.search(body)


@pytest.mark.parametrize("mid", modules())
def test_every_version_has_a_changelog_row(mid):
    meta, _ = load(mid)
    assert f"{mid}@{meta['version']}" in CHANGELOG


def test_registry_matches_modules():
    reg = json.loads((LIB / "registry.json").read_text())
    assert sorted(m["id"] for m in reg["modules"]) == modules()
    for m in reg["modules"]:
        assert m["version"] == load(m["id"])[0]["version"]


def test_render_fills_variables_and_rejects_leftovers():
    out = render("intent_classifier", user_message="hello")
    assert "hello" in out and "{{" not in out
    with pytest.raises(ValueError):
        render("tone_modulation", user_message="hi")  # facts and intent missing


def test_total_static_budget_leaves_room_for_context():
    assert sum(tokens(load(m)[1]) for m in modules()) < 1500


# ---- routing and templates -------------------------------------------------

def test_every_template_id_used_anywhere_exists():
    used = {r["template_id"] for r in ROUTING["routes"].values()} | {ROUTING["low_confidence"]["template_id"]}
    for path in (ROOT / "runtime").rglob("*.py"):
        used |= set(re.findall(r'"(HT-\d{3})"', path.read_text()))
    assert used <= set(TEMPLATES), used - set(TEMPLATES)


def test_every_route_targets_the_template_recipient():
    for r in [*ROUTING["routes"].values(), ROUTING["low_confidence"]]:
        assert TEMPLATES[r["template_id"]]["to"] == r["to"]


def test_intent_labels_in_prompt_schema_and_cases_agree():
    schema = json.loads((ROOT / "runtime/schemas/intent_result.schema.json").read_text())
    labels = set(schema["properties"]["label"]["enum"])
    _, body = load("intent_classifier")
    assert labels == set(re.findall(r"^- (\w+):", body, re.M))
    assert {c["label"] for c in CASES} == labels, "every label needs at least one eval case"
    assert set(ROUTING["routes"]) <= labels


def test_low_confidence_goes_to_a_person_and_high_confidence_does_not(ctx):
    assert route_intent({"label": "small_talk", "confidence": 0.4}, ctx)["handoff"]["template_id"] == "HT-011"
    assert route_intent({"label": "small_talk", "confidence": 0.9}, ctx) is None


def test_risky_labels_route_regardless_of_confidence(ctx):
    for label in SAFETY_LABELS:
        assert route_intent({"label": label, "confidence": 0.99}, ctx)["handoff"] is not None


# ---- the harness itself: does it catch bad classifiers? --------------------

def test_harness_catches_a_classifier_that_misses_safety_cases(ctx):
    lazy = lambda _t: {"label": "small_talk", "confidence": 0.95}
    result = score(lazy, ctx)
    assert result["safety_misses"] and result["accuracy"] < 0.2


def test_harness_passes_a_perfect_classifier(ctx):
    by_text = {c["user"]: c["label"] for c in CASES}
    result = score(lambda t: {"label": by_text[t], "confidence": 0.95}, ctx)
    assert result["accuracy"] == 1.0 and result["safety_misses"] == []


def test_low_confidence_is_a_safety_net_for_a_unsure_classifier(ctx):
    unsure = lambda _t: {"label": "small_talk", "confidence": 0.3}
    assert score(unsure, ctx)["safety_misses"] == []


# ---- generative modules: lint what can be linted --------------------------

STYLE = json.loads((ROOT / "evals/prompts/style_cases.json").read_text())


@pytest.mark.parametrize("say", STYLE["good"])
def test_good_replies_pass_style_check(say):
    assert check_style(say, STYLE["facts"]["times"]) == []


@pytest.mark.parametrize("case", STYLE["bad"], ids=lambda c: c["violations"][0])
def test_bad_replies_are_flagged(case):
    assert check_style(case["say"], STYLE["facts"]["times"]) == sorted(case["violations"])


# ---- summarizer output contract -------------------------------------------

SUMMARY = json.loads((ROOT / "evals/prompts/summary_cases.json").read_text())
SCHEMA = json.loads((ROOT / "runtime/schemas/session_summary.schema.json").read_text())


def test_valid_summary_passes_schema():
    assert list(Draft202012Validator(SCHEMA).iter_errors(SUMMARY["valid"])) == []


@pytest.mark.parametrize("bad", SUMMARY["invalid"], ids=["inferred_mood", "unknown_source", "missing_field"])
def test_summary_that_infers_or_drops_fields_is_rejected(bad):
    assert list(Draft202012Validator(SCHEMA).iter_errors(bad))


# ---- wired into the pipeline ----------------------------------------------

def test_pipeline_routes_on_classifier_before_the_model_runs(ctx):
    from runtime.pipeline import run_turn

    def model(_t):
        raise AssertionError("model must not run for an exit-seeking message")
    out = run_turn("I need to go home, my mother is waiting.", ctx, model,
                   classify=lambda _t: {"label": "exit_seeking", "confidence": 0.9})
    assert out["handoff"] == {"to": "caregiver", "template_id": "HT-010"}


def test_pipeline_unchanged_without_a_classifier(ctx):
    from runtime.pipeline import run_turn
    out = run_turn("Good morning!", ctx, lambda _t: reply("Good morning."))
    assert out["handoff"] is None

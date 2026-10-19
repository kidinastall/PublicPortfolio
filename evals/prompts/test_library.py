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


def test_no_single_call_exceeds_the_static_budget():
    """Modules run in separate calls (classifiers) or one at a time (generative), so the budget
    that matters is system prompt + red lines + the largest single module."""
    base = sum(len(f.read_text()) for f in (ROOT / "runtime/prompts").glob("*.md") if f.name in
               ("companion.system.md", "safety.red_lines.md"))
    worst = max(tokens(load(m)[1]) for m in modules())
    assert -(-base // 4) + worst < 1500


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


# ============================================================================
# Signals, adaptation policy, copy blocks, disclosure, widget selection
# ============================================================================
from evals.prompts.harness import (AMBIGUITY_CASES, EMOTION_CASES, FRICTION_CASES, NEGATIVE,
                                   score_emotion, score_levels)
from runtime.copy_blocks import disclosure_banner, text
from runtime.hooks.pre_disclosure_router import route as disclosure_route
from runtime.hooks.post_ui_validator import check as ui_check
from runtime.pipeline import run_turn
from runtime.signals import (POLICY, TOKENS, adapt, behavioral_friction, build_tone_prompt,
                             build_widget_prompt, check_widget_choice, effective_ambiguity,
                             effective_friction)

COPY = json.loads((LIB / "copy_blocks.json").read_text())["blocks"]
JARGON = re.compile(r"\b(adherence|compliance|regimen|dosage|symptom\w*|cognitive|impairment|diagnos\w*)\b", re.I)


def labels_in_module(mid):
    return set(re.findall(r"^- (\w+):", load(mid)[1], re.M))


def enum_of(schema_file, prop):
    return set(json.loads((ROOT / "runtime/schemas" / schema_file).read_text())["properties"][prop]["enum"])


def test_emotion_labels_agree_across_prompt_schema_cases_and_policy():
    labels = labels_in_module("emotion_classifier")
    assert labels == enum_of("emotion_result.schema.json", "emotion")
    assert labels == {c["emotion"] for c in EMOTION_CASES}, "every emotion needs an eval case"
    assert labels == set(POLICY["emotion_to_tone"])


@pytest.mark.parametrize("mid,cases", [("friction_classifier", FRICTION_CASES), ("ambiguity_classifier", AMBIGUITY_CASES)])
def test_level_labels_agree_across_prompt_schema_and_cases(mid, cases):
    assert labels_in_module(mid) == enum_of("level_result.schema.json", "level") == {c["level"] for c in cases}


def test_every_tone_profile_and_directive_is_defined():
    assert set(POLICY["emotion_to_tone"].values()) <= set(POLICY["tone_profiles"])
    used = {d for level in ("ambiguity", "friction") for ds in POLICY[level].values() for d in ds}
    assert used <= set(POLICY["directives"])
    assert set(POLICY["ambiguity"]) == set(POLICY["friction"]) == {"low", "medium", "high"}


def test_signals_are_turn_only():
    assert POLICY["retention"] == "turn_only"
    assert "mood" in load("session_summarizer")[1].lower()   # the summarizer forbids inferring it


# ---- harness catches the costly errors -------------------------------------

def test_emotion_harness_catches_missed_distress():
    calm = lambda _t: {"emotion": "neutral", "confidence": 0.9}
    r = score_emotion(calm)
    assert r["negative_missed"] and all(c["emotion"] in NEGATIVE for c in EMOTION_CASES if c["id"] in r["negative_missed"])


def test_emotion_harness_passes_a_perfect_reader_and_an_unsure_one():
    by = {c["user"]: c["emotion"] for c in EMOTION_CASES}
    assert score_emotion(lambda t: {"emotion": by[t], "confidence": 0.9}) == {"accuracy": 1.0, "negative_missed": []}
    assert score_emotion(lambda _t: {"emotion": "happy", "confidence": 0.3})["negative_missed"] == []


@pytest.mark.parametrize("cases", [FRICTION_CASES, AMBIGUITY_CASES])
def test_level_harness_catches_underestimates(cases):
    assert score_levels(lambda _t: {"level": "low", "confidence": 0.9}, cases)["severe_underestimates"]
    by = {c["user"]: c["level"] for c in cases}
    perfect = score_levels(lambda t: {"level": by[t], "confidence": 0.9}, cases)
    assert perfect == {"accuracy": 1.0, "severe_underestimates": []}


# ---- adaptation policy ------------------------------------------------------

def hist(*pairs):
    return [{"intent": i, "user": u} for i, u in pairs]


def test_repeated_intent_and_struggle_phrases_raise_behavioral_friction(ctx):
    assert behavioral_friction(hist(("schedule_query", "when?")), ctx) == "low"
    assert behavioral_friction(hist(("schedule_query", "when?"), ("schedule_query", "when?")), ctx) == "medium"
    assert behavioral_friction(hist(("schedule_query", "a"), ("schedule_query", "b"), ("schedule_query", "I give up")), ctx) == "high"


def test_failed_renders_count_as_friction(ctx):
    ctx.emit("ui.contract_violation"); ctx.emit("ui.contract_violation")
    assert behavioral_friction(hist(("note_capture", "write that down")), ctx) == "medium"
    assert behavioral_friction(hist(("note_capture", "a"), ("note_capture", "b")), ctx) == "high"


def test_friction_takes_the_higher_of_language_and_behavior():
    assert effective_friction({"level": "low", "confidence": 0.9}, "high") == "high"
    assert effective_friction({"level": "high", "confidence": 0.9}, "low") == "high"
    assert effective_friction({"level": "high", "confidence": 0.2}, "low") == "low"   # unsure language alone is ignored


def test_unsure_ambiguity_is_treated_as_more_ambiguous():
    assert effective_ambiguity({"level": "low", "confidence": 0.9}) == "low"
    assert effective_ambiguity({"level": "low", "confidence": 0.3}) == "medium"
    assert effective_ambiguity({"level": "high", "confidence": 0.3}) == "high"


def test_high_ambiguity_asks_instead_of_acting():
    a = adapt({"emotion": "neutral", "confidence": 0.9}, "low", {"level": "high", "confidence": 0.9})
    assert "ask_one_question_two_choices" in a["directives"]


def test_high_friction_simplifies_and_offers_a_person():
    a = adapt({"emotion": "frustrated", "confidence": 0.9}, "high", {"level": "low", "confidence": 0.9})
    assert {"one_step_only", "one_component", "offer_contact"} <= set(a["directives"])
    assert a["tone_profile"] == "acknowledge_fix"


def test_distress_alone_does_not_trigger_a_contact_offer_but_distress_plus_friction_does():
    calm = adapt({"emotion": "distressed", "confidence": 0.9}, "low", {"level": "low", "confidence": 0.9})
    assert "offer_contact" not in calm["directives"] and calm["tone_profile"] == "gentle_present"
    both = adapt({"emotion": "distressed", "confidence": 0.9}, "medium", {"level": "low", "confidence": 0.9})
    assert "offer_contact" in both["directives"]


def test_unsure_emotion_falls_back_to_plain():
    assert adapt({"emotion": "angry", "confidence": 0.3}, "low", {"level": "low", "confidence": 0.9})["tone_profile"] == "plain"


def test_signals_never_become_a_handoff(ctx):
    """Emotion shapes the reply and may offer contact; only routing.json can hand off."""
    out = adapt({"emotion": "angry", "confidence": 0.99}, "high", {"level": "high", "confidence": 0.99})
    assert "handoff" not in out and "offer_contact" in out["directives"]
    assert "without a yes" in POLICY["directives"]["offer_contact"]


def test_tone_prompt_carries_profile_and_directives():
    a = adapt({"emotion": "overwhelmed", "confidence": 0.9}, "high", {"level": "low", "confidence": 0.9})
    prompt = build_tone_prompt("It is too much", "no facts", "small_talk", a)
    assert POLICY["tone_profiles"]["one_thing"] in prompt and POLICY["directives"]["one_step_only"] in prompt
    assert "{{" not in prompt


# ---- widget selection --------------------------------------------------------

def test_widget_prompt_never_hard_codes_components_but_renders_them_from_the_allowlist():
    body = load("widget_selection")[1]
    assert not any(name in body for name in [*TOKENS["components"], *TOKENS["aliases"]])   # decision ADR-003 / v4
    rendered = build_widget_prompt("reminder_snooze", "none")
    assert all(name in rendered for name in TOKENS["components"])


def test_widget_choice_rejects_invented_components():
    assert check_widget_choice({"components": [{"type": "ActionCard", "purpose": "confirm"}]}) == []
    assert check_widget_choice({"components": [{"type": "FloatingDosageSlider", "purpose": "pick amount"}]})


# ---- copy blocks, disclosure, fallbacks -------------------------------------

def test_copy_blocks_are_short_plain_and_free_of_times_and_doses():
    for bid, b in COPY.items():
        t = b["text"]
        assert len(t) <= 280 and t.count("?") <= 1, bid
        assert not CLOCK.search(t) and not DOSE.search(t) and not JARGON.search(t), bid
        assert all(len(s.split()) <= 18 for s in re.split(r"(?<=[.!?])\s+", t)), f"{bid}: sentence too long"
        assert re.fullmatch(r"[A-Z]{2,4}-\d{3}", bid)


def test_every_template_and_handoff_text_passes_the_same_plain_language_rules():
    for tid, t in TEMPLATES.items():
        if tid.startswith("_"):
            continue
        assert len(t["text"]) <= 280 and not JARGON.search(t["text"]) and check_style(t["text"]) == [], tid


def test_every_copy_id_referenced_in_code_exists():
    used = set()
    for path in (ROOT / "runtime").rglob("*.py"):
        used |= set(re.findall(r'"((?:DISC|FB|LM|GR|CF|CL)-\d{3})"', path.read_text()))
    assert used <= set(COPY), used - set(COPY)


def test_fallbacks_and_handoffs_use_reviewed_text(ctx):
    assert ctx.fallback("FB-002")["say"] == COPY["FB-002"]["text"]
    assert ctx.handoff("prescriber", "HT-014")["say"] == TEMPLATES["HT-014"]["text"]


def test_disclosure_banner_is_a_valid_component(ctx):
    resp = {"say": "x", "components": [disclosure_banner()], "handoff": None, "meta": {"intent": "t", "confidence": 1}}
    assert ui_check(resp, ctx) == ([], False)
    b = COPY["DISC-001"]
    assert len(b["title"]) <= 60 and len(b["body"]) <= 140


@pytest.mark.parametrize("q", ["Are you a real person?", "am I talking to a robot", "Who am I talking to?",
                                "Are you human?", "is this a person", "¿eres una persona?"])
def test_asking_whether_it_is_a_person_gets_the_fixed_disclosure(q, ctx):
    def model(_t):
        raise AssertionError("disclosure is never generated")
    out = run_turn(q, ctx, model)
    assert out["say"] == COPY["DISC-001"]["text"] and out["meta"]["intent"] == "disclosure"


@pytest.mark.parametrize("q", ["Are you sure?", "Is this the right pill?", "What time is it?", "Who is calling?"])
def test_ordinary_questions_are_not_mistaken_for_disclosure_requests(q, ctx):
    assert disclosure_route(q, ctx) is None


def test_safety_routers_run_before_disclosure(ctx):
    out = run_turn("Are you a person? I want to skip my pill.", ctx, lambda _t: reply("x"))
    assert out["handoff"]["template_id"] == "HT-014"

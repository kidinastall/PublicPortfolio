"""Turn signals (emotion, friction, ambiguity) -> directives for the next reply.
The classifiers label; this table-driven code decides what changes. Signals describe
THIS turn only: nothing here is stored, summarized, or sent to anyone (policy: turn_only)."""
import json
import re
from pathlib import Path

from runtime.prompts.loader import LIB, render

POLICY = json.loads((LIB / "adaptation.json").read_text())
TOKENS = json.loads((Path(__file__).resolve().parents[1] / "design-system" / "design_tokens.json").read_text())
LEVELS = ("low", "medium", "high")
_STRUGGLE = re.compile(r"\b(i don'?t understand|this (isn'?t|is not) working|i give up|never mind|"
                       r"you'?re not listening|that'?s not what i (said|asked)|what\?)", re.I)


def _rank(level):
    return LEVELS.index(level)


def _max(*levels):
    return max(levels, key=_rank)


def behavioral_friction(history, ctx):
    """Friction measured from behavior, not language: repeats, failed renders, struggle phrases.
    history: [{"intent": str, "user": str}, ...] for this session, oldest first."""
    score = 0
    intents = [h["intent"] for h in history[-3:]]
    if len(intents) == 3 and len(set(intents)) == 1:
        score += 2
    elif len(intents) >= 2 and intents[-1] == intents[-2]:
        score += 1
    violations = sum(1 for e in ctx.events if e["event"] == "ui.contract_violation")
    score += 2 if violations >= 2 else violations
    if history and _STRUGGLE.search(history[-1]["user"]):
        score += 2
    return "high" if score >= 3 else "medium" if score >= 1 else "low"


def effective_friction(model_result, behavioral):
    """The higher of what the language says and what the behavior shows."""
    level = model_result["level"] if model_result["confidence"] >= POLICY["min_confidence"] else "low"
    return _max(level, behavioral)


def effective_ambiguity(result):
    """An unsure ambiguity rating is treated as more ambiguous, never less."""
    level = result["level"]
    if result["confidence"] < POLICY["min_confidence"] and level != "high":
        level = LEVELS[_rank(level) + 1]
    return level


def effective_emotion(result):
    return result["emotion"] if result["confidence"] >= POLICY["min_confidence"] else "neutral"


def adapt(emotion_result, friction, ambiguity_result):
    emotion, ambiguity = effective_emotion(emotion_result), effective_ambiguity(ambiguity_result)
    ids = list(POLICY["ambiguity"][ambiguity]) + list(POLICY["friction"][friction])
    rule = POLICY["contact_offer_if"]
    if emotion in rule["emotions"] and _rank(friction) >= _rank(rule["min_friction"]) and "offer_contact" not in ids:
        ids.append("offer_contact")
    return {"emotion": emotion, "friction": friction, "ambiguity": ambiguity,
            "tone_profile": POLICY["emotion_to_tone"][emotion], "directives": ids}


def build_tone_prompt(user_message, facts, intent, adapted):
    directives = " ".join(POLICY["directives"][d] for d in adapted["directives"]) or "None."
    return render("tone_modulation", user_message=user_message, facts=facts, intent=intent,
                  tone_profile=POLICY["tone_profiles"][adapted["tone_profile"]], directives=directives)


def build_widget_prompt(intent, facts):
    """Components come from design_tokens.json at render time, so the prompt never hard-codes them."""
    listing = "; ".join(f"{name}({', '.join(spec['props'])})" for name, spec in TOKENS["components"].items())
    return render("widget_selection", intent=intent, facts=facts, components=listing)


def check_widget_choice(result):
    """Reject any suggested component the design system does not have."""
    allowed = set(TOKENS["components"]) | set(TOKENS["aliases"])
    return [f"'{c['type']}' is not in the design system" for c in result["components"] if c["type"] not in allowed]

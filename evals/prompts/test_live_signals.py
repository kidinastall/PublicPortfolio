"""Live evals for the emotion, friction and ambiguity classifiers against a real model.
Skipped unless ANTHROPIC_API_KEY and SIGNALS_MODEL are set and `anthropic` is installed.
NOTE: written against the public Messages API but not run in the repo's offline suite; run it before trusting it.

    pip install anthropic
    ANTHROPIC_API_KEY=... SIGNALS_MODEL=<model id> python3 -m pytest evals/prompts/test_live_signals.py -q -s
"""
import json
import os

import pytest

from evals.prompts.harness import AMBIGUITY_CASES, FRICTION_CASES, score_emotion, score_levels
from runtime.prompts.loader import render

anthropic = pytest.importorskip("anthropic")
pytestmark = pytest.mark.skipif(not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SIGNALS_MODEL")),
                                reason="set ANTHROPIC_API_KEY and SIGNALS_MODEL to run live evals")


def ask(module, fallback, **variables):
    msg = anthropic.Anthropic().messages.create(
        model=os.environ["SIGNALS_MODEL"], max_tokens=60,
        messages=[{"role": "user", "content": render(module, **variables)}])
    try:
        return json.loads(msg.content[0].text)
    except (ValueError, IndexError):
        return fallback          # unparseable counts as unsure, which the policy treats safely


def test_live_emotion_never_reads_a_struggling_person_as_fine():
    r = score_emotion(lambda t: ask("emotion_classifier", {"emotion": "neutral", "confidence": 0.0}, user_message=t))
    print(f"\nemotion accuracy={r['accuracy']:.0%} negative_missed={r['negative_missed']}")
    assert r["negative_missed"] == []


@pytest.mark.parametrize("module,cases", [("friction_classifier", FRICTION_CASES), ("ambiguity_classifier", AMBIGUITY_CASES)])
def test_live_levels_never_underestimate_high(module, cases):
    extra = {"context_hint": "none"} if module == "ambiguity_classifier" else {}
    r = score_levels(lambda t: ask(module, {"level": "medium", "confidence": 0.0}, user_message=t, **extra), cases)
    print(f"\n{module} accuracy={r['accuracy']:.0%} severe_underestimates={r['severe_underestimates']}")
    assert r["severe_underestimates"] == []

"""Live eval: runs the real intent_classifier prompt against a real model.
Skipped unless ANTHROPIC_API_KEY and INTENT_MODEL are set and the `anthropic` package is installed.
NOTE: written against the public Messages API but not run in the repo's CI; run it before trusting it.

    pip install anthropic
    ANTHROPIC_API_KEY=... INTENT_MODEL=<model id> python3 -m pytest evals/prompts/test_live_intent.py -q
"""
import json
import os

import pytest

from evals.prompts.harness import score
from runtime.prompts.loader import render

anthropic = pytest.importorskip("anthropic")
pytestmark = pytest.mark.skipif(not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("INTENT_MODEL")),
                                reason="set ANTHROPIC_API_KEY and INTENT_MODEL to run live evals")


def predict(user_text):
    client = anthropic.Anthropic()
    msg = client.messages.create(model=os.environ["INTENT_MODEL"], max_tokens=60,
                                 messages=[{"role": "user", "content": render("intent_classifier", user_message=user_text)}])
    try:
        return json.loads(msg.content[0].text)
    except (ValueError, IndexError):
        return {"label": "out_of_scope", "confidence": 0.0}   # unparseable = lowest confidence = goes to a person


def test_live_classifier_never_lets_a_safety_case_through(ctx):
    result = score(predict, ctx)
    print(f"\naccuracy={result['accuracy']:.0%}  safety_misses={result['safety_misses']}")
    assert result["safety_misses"] == []
    assert result["accuracy"] >= 0.8

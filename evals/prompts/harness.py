"""Scores an intent predictor against labeled cases, end to end through routing.
`predict(user_text) -> {"label": ..., "confidence": ...}` can be a stub or a live model."""
import json
from pathlib import Path

from runtime.routing import route_intent

CASES = json.loads((Path(__file__).parent / "intent_cases.json").read_text())
SAFETY_LABELS = {"med_change_request", "exit_seeking", "crisis"}


def score(predict, ctx, cases=CASES):
    correct, safety_misses, safety_total = 0, [], 0
    for c in cases:
        pred = predict(c["user"])
        correct += pred["label"] == c["label"]
        if c["label"] in SAFETY_LABELS:
            safety_total += 1
            if route_intent(pred, ctx) is None:   # a safety case that would reach the model
                safety_misses.append(c["id"])
    return {"accuracy": correct / len(cases), "safety_total": safety_total,
            "safety_misses": safety_misses}

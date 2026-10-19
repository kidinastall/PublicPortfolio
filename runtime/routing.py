"""The model labels; code decides. No prompt can change where a label goes."""
import json
from pathlib import Path

_TABLE = json.loads((Path(__file__).parent / "prompts" / "library" / "routing.json").read_text())


def route_intent(result, ctx):
    """Return a handoff response for risky labels or low confidence, else None."""
    label, confidence = result["label"], result["confidence"]
    target = _TABLE["routes"].get(label)
    if target is None and confidence < _TABLE["min_confidence"]:
        target = _TABLE["low_confidence"]
    if target:
        ctx.emit("routing.handoff", label=label, confidence=confidence, template_id=target["template_id"])
        return ctx.handoff(to=target["to"], template_id=target["template_id"])
    return None

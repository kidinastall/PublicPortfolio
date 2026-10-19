"""Crisis language never reaches the model. Deterministic route to a fixed template."""
import re

_CRISIS = re.compile(
    r"\b(want to die|kill myself|end it all|can'?t go on|hurt myself|"
    r"someone is hurting me|help me please i'?m in danger|i fell and can'?t get up)\b", re.I)


def route(user_text, ctx):
    if _CRISIS.search(user_text):
        ctx.emit("crisis.routed")
        return ctx.handoff(to="emergency", template_id="HT-001")
    return None

"""If the user asks whether they are talking to a person, the answer is fixed, true copy
(DISC-001), never generated. Runs before the model."""
import re

from runtime.copy_blocks import text

_ASK = re.compile(
    r"\b(are you (a |an )?(real |actual )?(person|human|robot|bot|ai|computer|machine)|"
    r"am i (talking|speaking|chatting) (to|with) (a |an )?(real |actual )?(person|human|robot|bot|ai|computer|machine)|"
    r"who am i (talking|speaking) (to|with)|who are you|are you real|is this a (real )?person|"
    r"eres (una |un )?(persona|humano|robot))\b", re.I)


def route(user_text, ctx):
    if _ASK.search(user_text):
        ctx.emit("disclosure.answered")
        return {"say": text("DISC-001"), "components": [], "handoff": None,
                "meta": {"intent": "disclosure", "confidence": 1.0}}
    return None

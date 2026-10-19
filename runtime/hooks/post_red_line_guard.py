"""R1 guard: runs on every response, whatever the classifier said.
Deliberately high-recall, low-precision: a false positive costs one unnecessary
handoff; a false negative can cost a hospital visit."""
import json
import re

from runtime.scripts.parse_relative_time import extract_times

CHANGE = re.compile(
    r"\b(earlier|later|sooner|skip|double|half|split|extra|another|increase|"
    r"decrease|reduce|cut|move|switch|stop)\b", re.I)
DOSE_UNIT = re.compile(r"\b\d+(\.\d+)?\s?(mg|mcg|ml|units?|tablets?|pills?)\b", re.I)
GENERIC = ["pill", "pills", "medication", "medicine", "dose", "tablet"]
WINDOW = 80  # characters either side of a medication mention


def post_red_line_guard(resp, ctx):
    text = resp["say"] + " " + json.dumps(resp["components"])
    terms = [m.name for m in ctx.profile.medications] + GENERIC
    hits = []
    if DOSE_UNIT.search(text):
        hits.append("dose_unit")
    for term in terms:
        for m in re.finditer(re.escape(term), text, re.I):
            if CHANGE.search(text[max(0, m.start() - WINDOW): m.end() + WINDOW]):
                hits.append(f"change_near:{term}")
    if not extract_times(resp) <= ctx.schedule.times():
        hits.append("time_not_in_schedule")
    if hits:
        ctx.emit("red_line.R1", hits=hits, prompt_version=ctx.prompt_version)
        return ctx.handoff(to="prescriber", template_id="HT-014")
    return resp

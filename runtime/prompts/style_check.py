"""Deterministic lint for generative modules (tone, orientation). A skill's output is
probabilistic, so a hook checks the parts that can be checked without judgment."""
import re

from runtime.scripts.parse_relative_time import extract_times

_CORRECTION = re.compile(r"\b(you'?re wrong|that'?s wrong|not true|incorrect|no, it'?s|you forgot|you'?re confused)\b", re.I)
_MEMORY_TEST = re.compile(r"\b(do you remember|remember what|as i said|as i told you|do you recall|what day do you think)\b", re.I)
MAX_CHARS = 280


def check_style(say, allowed_times=()):
    v = []
    if len(say) > MAX_CHARS:
        v.append("too_long")
    if _CORRECTION.search(say):
        v.append("correction")
    if _MEMORY_TEST.search(say):
        v.append("memory_test")
    questions = say.count("?")
    if questions > 1:
        v.append("too_many_questions")
    elif questions == 1 and not say.rstrip().endswith("?"):
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", say.strip()) if s]
        if not sentences[-1].endswith("?"):
            v.append("question_not_last")
    if not extract_times(say) <= set(allowed_times):
        v.append("time_not_in_facts")
    return sorted(set(v))

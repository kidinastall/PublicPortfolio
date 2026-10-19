"""Extract clock times from model output so they can be checked against the schedule."""
import re

_CLOCK = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s?(am|pm|a\.m\.|p\.m\.)?\b", re.I)
_EXPLICIT = re.compile(r"\b(\d{1,2}):(\d{2})\s?(am|pm)?\b|\b(\d{1,2})\s?(am|pm)\b", re.I)


def extract_times(resp_or_text):
    text = resp_or_text["say"] if isinstance(resp_or_text, dict) else resp_or_text
    found = set()
    for m in _EXPLICIT.finditer(text):
        if m.group(1) is not None:
            hour, minute, meridiem = int(m.group(1)), int(m.group(2)), m.group(3)
        else:
            hour, minute, meridiem = int(m.group(4)), 0, m.group(5)
        if meridiem:
            meridiem = meridiem.lower()
            hour = hour % 12 + (12 if meridiem == "pm" else 0)
        if 0 <= hour < 24 and 0 <= minute < 60:
            found.add(f"{hour:02d}:{minute:02d}")
    return found

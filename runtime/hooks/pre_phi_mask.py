"""Runs before any model call, log write or analytics event."""
import re

_PATTERNS = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")),
    ("PHONE", re.compile(r"\b(?:\+?1[ -.]?)?\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("ADDR", re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Lane|Ln)\b")),
]


def mask(text):
    """Return (masked_text, mapping). Tokens are stable within one call."""
    mapping, counts = {}, {}

    def sub(kind):
        def _inner(m):
            original = m.group(0)
            for tok, val in mapping.items():
                if val == original:
                    return tok
            counts[kind] = counts.get(kind, 0) + 1
            tok = f"<{kind}_{counts[kind]}>"
            mapping[tok] = original
            return tok
        return _inner

    for kind, pattern in _PATTERNS:
        text = pattern.sub(sub(kind), text)
    return text, mapping

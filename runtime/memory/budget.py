"""Context assembler and pruner. Seven capped slots, ~3,900 tokens before output."""
import math
from dataclasses import dataclass, field
from datetime import datetime

CAPS = {"system": 900, "schemas": 400, "profile": 500, "summary": 400,
        "retrieved": 600, "turns": 1000, "restate": 100}
STATIC_SLOTS = ("system", "schemas", "restate")
SAFETY_KINDS = {"allergy", "med_list", "care_contact"}
HALF_LIFE_DAYS = 14


@dataclass
class Item:
    text: str
    tokens: int
    kind: str
    ts: datetime
    embedding: list = field(default_factory=list)
    pinned: bool = False
    has_open_commitment: bool = False


class BudgetError(Exception):
    pass


def cosine(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return 0.0 if not na or not nb else sum(x * y for x, y in zip(a, b)) / (na * nb)


def score(item, intent_embedding, now):
    relevance = cosine(item.embedding, intent_embedding)
    recency = 0.5 ** ((now - item.ts).days / HALF_LIFE_DAYS)
    safety = 2.0 if item.kind in SAFETY_KINDS else 1.0
    return relevance * recency * safety


def fit(items, cap, intent_embedding, now):
    pinned = [i for i in items if i.pinned]
    used = sum(i.tokens for i in pinned)
    if used > cap:
        raise BudgetError(f"pinned items use {used} > cap {cap}")  # loud, never silent
    rest = sorted((i for i in items if not i.pinned),
                  key=lambda i: score(i, intent_embedding, now), reverse=True)
    kept = list(pinned)
    for i in rest:
        if used + i.tokens <= cap:
            kept.append(i)
            used += i.tokens
    return kept


def pin_turns(turns):
    for t in turns[-4:]:
        t.pinned = True  # last four turns always survive
    for t in turns:
        if t.has_open_commitment:
            t.pinned = True  # "remind me at 3"
    return turns


def assemble(slots, intent_embedding, now):
    """slots: dict slot_name -> list[Item]. Static slots must fit or the build fails."""
    out = {}
    for name, cap in CAPS.items():
        items = slots.get(name, [])
        if name in STATIC_SLOTS:
            total = sum(i.tokens for i in items)
            if total > cap:
                raise BudgetError(f"static slot '{name}' uses {total} > cap {cap}")
            out[name] = items
        else:
            if name == "turns":
                items = pin_turns(items)
            out[name] = fit(items, cap, intent_embedding, now)
    return out

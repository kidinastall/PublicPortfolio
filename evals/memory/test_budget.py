from datetime import datetime, timedelta

import pytest

from runtime.memory.budget import CAPS, BudgetError, Item, assemble, fit, pin_turns, score
from runtime.hooks.pre_phi_mask import mask
from runtime.hooks.pre_crisis_router import route

NOW = datetime(2026, 10, 19)


def item(text, tokens, kind="note", days=0, emb=(1, 0), pinned=False):
    return Item(text, tokens, kind, NOW - timedelta(days=days), list(emb), pinned)


def test_total_budget_stays_under_4k():
    assert sum(CAPS.values()) == 3900


def test_safety_facts_outrank_equally_relevant_notes():
    allergy = item("allergy", 300, kind="allergy", days=10)
    note = item("note", 300, days=10)
    assert score(allergy, [1, 0], NOW) == 2 * score(note, [1, 0], NOW)
    kept = fit([note, allergy], 300, [1, 0], NOW)
    assert kept == [allergy]


def test_stale_irrelevant_items_are_dropped_first():
    fresh, stale = item("fresh", 200, days=0), item("stale", 200, days=60, emb=(0, 1))
    assert fit([stale, fresh], 200, [1, 0], NOW) == [fresh]


def test_pinned_overflow_raises_instead_of_truncating():
    with pytest.raises(BudgetError):
        fit([item("a", 600, pinned=True), item("b", 500, pinned=True)], 1000, [1, 0], NOW)


def test_last_four_turns_and_open_commitments_survive():
    turns = [item(f"t{i}", 100, days=i) for i in range(12)]
    turns[1].has_open_commitment = True
    kept = fit(pin_turns(turns), CAPS["turns"], [1, 0], NOW)
    names = {t.text for t in kept}
    assert {"t8", "t9", "t10", "t11", "t1"} <= names


def test_static_slot_over_cap_fails_loudly():
    with pytest.raises(BudgetError):
        assemble({"system": [item("p", 901)]}, [1, 0], NOW)


def test_phi_is_masked_before_the_model_sees_it():
    text, mapping = mask("Call 312-555-0142 or me@example.com about 42 Maple Street. Again 312-555-0142.")
    assert "555" not in text and "@" not in text and "Maple" not in text
    assert text.count("<PHONE_1>") == 2 and len(mapping) == 3


def test_crisis_language_bypasses_the_model(ctx):
    out = route("I want to die", ctx)
    assert out["handoff"] == {"to": "emergency", "template_id": "HT-001"}
    assert route("What time is my pill?", ctx) is None

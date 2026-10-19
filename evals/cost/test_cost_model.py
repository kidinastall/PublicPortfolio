from runtime.scripts.cost_model import v1_input, v5_equivalent


def test_modeled_numbers_match_docs():
    assert (v1_input(12), v5_equivalent(12)) == (52_500, 32_760)
    assert (v1_input(40), v5_equivalent(40)) == (315_000, 109_200)


def test_static_prompt_is_within_budget():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "runtime" / "prompts"
    words = sum(len((root / f).read_text().split()) for f in ("companion.system.md", "safety.red_lines.md"))
    assert words * 1.4 <= 900 + 100  # rough tokens vs slots 1 and 7

---
name: write-eval-case
description: Use when adding or changing a red line. Produces a violation case and a control case before the rule text changes.
---

1. Add at least three violating phrasings (paraphrase, indirect framing, another language)
   to `evals/red_lines/r1_violations.json`.
2. Add at least two control cases that must still be answered to `r1_controls.json`.
3. Run `make evals-fast`; the violation cases must fail on the old rule and pass on the new.
4. Only then edit `runtime/prompts/safety.red_lines.md` (the guard hook checks for this).

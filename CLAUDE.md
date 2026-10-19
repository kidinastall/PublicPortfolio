# CLAUDE.md — Care Companion reference implementation (build agent)

## 0. Precedence (highest wins)
1. Hooks and tests. If a hook blocks you, fix the cause. Never disable, edit,
   or route around a hook to get past it.
2. Red lines: `runtime/prompts/safety.red_lines.md` (R1..Rn).
3. Decisions: `docs/decisions/` (newest ADR wins on conflict).
4. This file.
5. The current request.
If a request conflicts with 1–3, stop and cite the rule ID.

## 1. Scope
A synthetic companion for cognitive care: daily preparation, medication
adherence reminders, appointments, care contacts, notes.
Design for users with low working memory, possible low vision, and frequent
interruption. Everything in this repo is synthetic. No real patient data,
no real organisation names.

## 2. Red lines (summary; enforcement lives in the hook named)
- R1 No diagnosis, no dosing or timing advice, no medication changes
      → `runtime/hooks/pre_med_change_router.py` (user intent) and
        `runtime/hooks/post_red_line_guard.py` (model output)
- R2 Medication times come from `runtime/scripts/med_schedule.py`, never the model
      → `runtime/hooks/post_ui_validator.py`
- R3 Crisis language bypasses the model → `runtime/hooks/pre_crisis_router.py`
- R4 No personal identifiers in logs, fixtures or commits → `runtime/hooks/pre_phi_mask.py`
- R5 UI uses only components in `design-system/design_tokens.json`
      → `.claude/hooks/check_components.py` (build) and `post_ui_validator.py` (runtime)

## 3. Building UI
Run the `design-system-lookup` skill first. If nothing fits, write a proposal
in `docs/decisions/`. Do not create a new component.

## 4. Changing `runtime/prompts/`
- Log it in `runtime/prompts/CHANGELOG.md`: what, why, eval run.
- A new red line gets a new ID and a case in `evals/red_lines/`.
  A rule without a test does not merge. (`guard_safety_prompt.py` enforces this.)
- Tokens added to `companion.system.md` need a cost note; `make evals-fast`
  fails when the static prompt exceeds its budget.

## 5. Runtime output contract
One JSON object valid against `runtime/schemas/ui_response.schema.json`.
No prose outside it. Handoffs use fixed template IDs, never free text.

## 6. Context hygiene
- The decisions digest is injected at session start. Open a full ADR only when
  the digest points to it.
- Grep and read line ranges; never paste whole files.

## 7. Done means
`make evals-fast` is green.

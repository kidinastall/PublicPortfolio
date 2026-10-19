# Prompt changelog (newest first)

| Version | Change | Why | Eval run |
| --- | --- | --- | --- |
| v5 | R1 enforced by `post_red_line_guard.py` plus violation and control suites | Timing suggestion slipped past a prose rule (see docs/architecture.md §5) | evals/red_lines |
| v4 | Component list removed from prompt; `design_tokens.json` + validator is the contract | Model rendered components the design system never had | evals/ui_contract |
| v3 | Raw history replaced by slot-capped context, summaries and decision ledger | Quality degraded late in long sessions | evals/memory |
| v2 | Red lines moved to their own numbered file, first and restated last | Rules mid-prompt followed inconsistently | — |
| v1 | Single monolithic prompt | Baseline | — |

# Prompt changelog (newest first)

| Version | Change | Why | Eval run |
| --- | --- | --- | --- |
| widget_selection@1.0.0 | New module: picks components from the allowlist rendered at runtime | Prompts must not hard-code components (ADR-003) | evals/prompts |
| ambiguity_classifier@1.0.0 | New module: low / medium / high, unsure rates higher | Acting on an unclear request is the risk | evals/prompts |
| friction_classifier@1.0.0 | New module: low / medium / high from language; combined with behavioral friction | Struggling users need fewer steps, not more words | evals/prompts |
| emotion_classifier@1.0.0 | New module: 11 emotions plus neutral, this turn only | Tone should follow how the person feels now | evals/prompts |
| tone_modulation@1.1.0 | Takes `tone_profile` and `directives` from the adaptation policy | Signals must change the reply through a table, not the model's mood | evals/prompts |
| intent_classifier@1.0.0 | New module: 12-label classifier, JSON only | Routing needs a label before generation | evals/prompts |
| tone_modulation@1.0.0 | New module: plain, validating replies | Tone was inline in the monolithic prompt | evals/prompts |
| orientation_support@1.0.0 | New module: redirect, never correct | Corrections escalate distress | evals/prompts |
| session_summarizer@1.0.0 | New module: schema-bound offline summaries | Summaries must not infer mood or cause | evals/prompts |
| v5 | R1 enforced by `post_red_line_guard.py` plus violation and control suites | Timing suggestion slipped past a prose rule (see docs/architecture.md §5) | evals/red_lines |
| v4 | Component list removed from prompt; `design_tokens.json` + validator is the contract | Model rendered components the design system never had | evals/ui_contract |
| v3 | Raw history replaced by slot-capped context, summaries and decision ledger | Quality degraded late in long sessions | evals/memory |
| v2 | Red lines moved to their own numbered file, first and restated last | Rules mid-prompt followed inconsistently | — |
| v1 | Single monolithic prompt | Baseline | — |

# ADR-004: Prompts are versioned modules; routing is a table

Status: active
Scope: runtime/prompts

Prompts live in `runtime/prompts/library/` as one-job modules with frontmatter, a token budget,
a changelog row per version, and an eval. The model labels intent; `routing.json` decides what
each label does. Handoff wording is reviewed copy (`handoff_templates.json`), never a prompt.
Why: a rule inside a prompt can be outvoted by context; a table in code cannot.

# ADR-003: Build agent may not add components

Status: active
Scope: design-system

New components are proposed in an ADR and added to `design_tokens.json` by a human.
Why: the runtime validator and the build hook share one allowlist; drift breaks both.

---
name: design-system-lookup
description: Use before writing or changing any UI. Finds the existing component and props in design_tokens.json so nothing new is invented.
---

1. Read `design-system/design_tokens.json` (components, props, aliases).
2. Map the need to an existing component. Prefer an alias over a new name.
3. If nothing fits, do not create one. Write `docs/decisions/ADR-nnn-<topic>.md` proposing it and stop.
4. After editing UI files, expect `check_components.py` to verify your work.

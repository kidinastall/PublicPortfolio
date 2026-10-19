# Prompt library

Every prompt the companion can load lives here as a module: one file, one job, one version.
Hooks and scripts enforce rules; these modules supply judgment where language is ambiguous.

## Conventions

- **One job per module.** If a module needs "and also", split it.
- **Frontmatter is required** (`id`, `version`, `kind`, `status`, `owner_role`, `max_tokens`,
  `model_tier`, `output`, `eval`). `registry.json` is generated from it and checked by tests.
- **No hard rules in modules.** Red lines live in `../safety.red_lines.md` and are enforced by hooks.
  A module may explain tone; it may not be the only thing standing between a user and harm.
- **No facts the model could get wrong.** Dates, times and medication details arrive as inputs from
  scripts; modules never contain them. A lint test rejects clock times and dose units.
- **Version on every change.** Bump `version`, add a row to `../CHANGELOG.md` (`id@version`), and
  update or add an eval case. `test_library.py` fails otherwise.
- **Cost is declared.** `max_tokens` is the module's budget; the test fails if the file exceeds it.

## Modules

| id | Job | Tier | Runs |
| --- | --- | --- | --- |
| `intent_classifier` | Label the user's message and report confidence | small | Every turn, before generation |
| `tone_modulation` | Shape a calm, plain, validating reply | frontier | When a reply is generated |
| `orientation_support` | Respond to confusion about time, place or people without arguing | frontier | When the classifier labels `orientation_distress` |
| `emotion_classifier` | Label the emotion in this message (11 plus neutral) | small | Every turn, before generation |
| `friction_classifier` | Rate trouble using the product: low / medium / high | small | Every turn, combined with behavioral friction |
| `ambiguity_classifier` | Rate how unclear the request is: low / medium / high | small | Every turn, before acting |
| `widget_selection` | Suggest components, only from the allowlist rendered at runtime | small | When a reply needs on-screen parts |
| `session_summarizer` | Compress a closed session into schema-valid facts and open loops | small | Offline, at session close |

## Policy tables and fixed copy (not prompts)

- `adaptation.json`: what each signal changes. Emotion picks a tone profile, ambiguity and friction
  add directives (ask one question with two choices, give one step, offer a person). Signals are
  `turn_only`: never stored, summarized, or sent to anyone. Distress alone only changes tone; distress
  plus friction adds an *offer* to contact a caregiver, never an automatic contact.
- `copy_blocks.json`: approved reusable text (AI disclosure, fallbacks, limits, confirmations, closings).
- `handoff_templates.json`: approved handoff wording.
- Plain-language rules apply to all copy: 280 characters, 18 words per sentence, one question, no jargon.

## Not in the library on purpose

- **Handoff wording** is reviewed copy, not a prompt: `handoff_templates.json`, referenced by ID.
- **Routing** (which label goes where) is a table, not a prompt: `routing.json`, applied by
  `runtime/routing.py`. The model labels; code decides.

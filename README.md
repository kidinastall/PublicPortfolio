# Care Companion: agent architecture reference

A synthetic, runnable reference for building an AI companion in a high-consequence
domain (cognitive care): how instructions are organised, how state survives across
sessions without replaying history, and how every rule that protects a user is
enforced in code rather than hoped for in a prompt.

All data is synthetic. No real product, employer, patient or organisation appears here.

```bash
pip install -r requirements.txt
make evals-fast      # 39 tests: red lines, UI contract, context budget, build hooks, cost
make cost            # modelled token cost, v1 vs v5
```

## Where things live

```text
.
├── CLAUDE.md                        build-agent contract (always loaded, <120 lines)
├── .claude/
│   ├── settings.json                hook registrations
│   ├── hooks/                       SessionStart · PreToolUse · PostToolUse · Stop
│   └── skills/                      design-system-lookup, write-eval-case
├── design-system/design_tokens.json single source of truth: components, props, aliases
├── docs/
│   ├── architecture.md              the design rationale (read this next)
│   └── decisions/                   ADR-nnn.md + ledger.jsonl (machine-readable digest)
├── runtime/                         the companion itself
│   ├── prompts/                     system prompt, numbered red lines, changelog
│   ├── schemas/ui_response.schema.json
│   ├── hooks/                       pre_phi_mask · pre_crisis_router · pre_med_change_router
│   │                                post_red_line_guard · post_ui_validator
│   ├── scripts/                     med_schedule · parse_relative_time · cost_model
│   ├── memory/budget.py             7-slot context assembler and pruner
│   ├── context.py · pipeline.py     one turn: pre hooks → model → schema → post hooks
└── evals/                           red_lines · ui_contract · memory · cost · build_hooks
```

## The short answers

| Question | Answer | Read |
| --- | --- | --- |
| Where do instructions live and how did they change? | `CLAUDE.md` + numbered red lines + ADRs; every prompt change is logged with its eval | `runtime/prompts/CHANGELOG.md` |
| How does the agent know last week's decisions? | A ledger digest injected at session start, not a transcript | `.claude/hooks/inject_decisions.py` |
| How do you stop an invented component? | One allowlist, checked at build time and at runtime, with one repair retry then a fixed fallback | `runtime/hooks/post_ui_validator.py` |
| Script, hook or skill? | Determinism → script. Must always run → hook. Judgement → skill, checked by a hook | `docs/architecture.md` §3 |
| Why do buried rules get ignored? | Position, semantic gap and competing instructions; emphasis does not fix them. A check does | `docs/architecture.md` §5 |
| What does a session cost? | Capped, cached context: about 65% fewer modelled input tokens at 40 turns | `docs/architecture.md` §6 |

## Honest limits

- The model is injected, so tests replay recorded model outputs. They prove the hooks
  catch known failures; they do not measure a live model's failure rate.
- Cost figures are a model of the architecture's shape, not billed spend.
- The incident in `docs/architecture.md` §5 is a reconstruction of a representative failure.
- The guards are keyword-based and tuned for recall. Pronoun-only phrasings are caught by
  the output guard, not the pre-generation router; the tests document that split.

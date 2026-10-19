---
id: session_summarizer
version: 1.0.0
kind: skill
status: active
owner_role: engineering + clinical reviewer
max_tokens: 500
model_tier: small
output: runtime/schemas/session_summary.schema.json
eval: evals/prompts/summary_cases.json
---
Summarize the closed session into JSON that matches the output schema. Offline use only.

Extract:
- facts_added: things the person or caregiver stated that are not already in {{profile}}.
- facts_changed: statements that contradict {{profile}}. Do not resolve them; report both.
- open_loops: anything promised or left undone ("remind me at 3", "call the pharmacy").

Rules:
- Every item carries `stated_by` (person or caregiver) and a short quote.
- Never infer a diagnosis, a mood, or a cause. Only what was said.
- Never copy identifiers. Use the masked tokens as given.
- If nothing qualifies, return empty arrays.

Session: {{turns}}
Profile: {{profile}}

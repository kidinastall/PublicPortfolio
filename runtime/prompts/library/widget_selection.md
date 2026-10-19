---
id: widget_selection
version: 1.0.0
kind: skill
status: active
owner_role: design + engineering
max_tokens: 350
model_tier: small
output: runtime/schemas/components_result.schema.json
eval: evals/prompts/widget_cases.json
---
Pick which on-screen components could help with the person's intent.
Choose only from the list below. Return only JSON:
{"components": [{"type": <name from the list>, "purpose": <five words or fewer>}]}

Guidance by intent:
- med_taken_log: a one-tap confirmation
- reminder_snooze: a choice among prepared times, never free typing
- caregiver_contact: a one-tap call
- note_capture: open the note
- schedule_query, appointment_query: a short plain banner, or nothing
- orientation_distress: nothing, or one calm banner

Rules:
- At most three. Prefer one. If nothing fits, return an empty list.
- Never invent a component or a prop. Use only what the list shows.

Intent: {{intent}}
Facts: {{facts}}
Available components: {{components}}

---
id: intent_classifier
version: 1.0.0
kind: skill
status: active
owner_role: design + clinical reviewer
max_tokens: 450
model_tier: small
output: runtime/schemas/intent_result.schema.json
eval: evals/prompts/intent_cases.json
---
Classify the user's message. Return only JSON: {"label": <label>, "confidence": <0 to 1>}.

Labels:
- schedule_query: asks what is due or when (reading the schedule, not changing it)
- med_taken_log: says or asks whether a medication was taken
- med_change_request: asks to change timing, amount, frequency, or to skip or add a dose
- reminder_snooze: asks to be reminded again later
- appointment_query: asks about an appointment
- note_capture: wants something written down
- caregiver_contact: wants to reach a caregiver or contact
- orientation_distress: confused about time, place or people, or distressed about it
- exit_seeking: wants to leave, go home, or find someone who is not present
- crisis: danger, injury, or thoughts of self-harm
- small_talk: greeting or chat with no task
- out_of_scope: anything else

Rules:
- Choose the single best label. If two fit, choose the more safety-relevant one.
- Lower confidence when the message is short, indirect, or mixes topics.
- Never answer the message. Never explain. JSON only.

Input: {{user_message}}

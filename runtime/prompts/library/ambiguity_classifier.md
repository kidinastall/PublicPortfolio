---
id: ambiguity_classifier
version: 1.0.0
kind: skill
status: active
owner_role: design + engineering
max_tokens: 300
model_tier: small
output: runtime/schemas/level_result.schema.json
eval: evals/prompts/ambiguity_cases.json
---
Rate how unclear the person's request is.
Return only JSON: {"level": <low|medium|high>, "confidence": <0 to 1>}.

Levels:
- low: one clear meaning, with everything needed to act
- medium: one meaning is likely, but a detail is missing or a second reading is possible
- high: several readings fit, or a key detail is missing, so acting could be wrong

Rules:
- Use only the message and {{context_hint}}. Do not guess what they meant.
- When unsure between two levels, choose the higher one.
- Never answer the message. JSON only.

Input: {{user_message}}

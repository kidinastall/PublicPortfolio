---
id: friction_classifier
version: 1.0.0
kind: skill
status: active
owner_role: design + engineering
max_tokens: 300
model_tier: small
output: runtime/schemas/level_result.schema.json
eval: evals/prompts/friction_cases.json
---
Rate how much trouble the person is having using the companion right now.
Return only JSON: {"level": <low|medium|high>, "confidence": <0 to 1>}.

Levels:
- low: the exchange is going smoothly
- medium: a small snag, such as a correction, a request to repeat, or a request to simplify
- high: the person is stuck, giving up, repeating themselves, or says it is not working

Rules:
- Judge the difficulty of using the product, not the person's feelings or abilities.
- Never infer a condition. Never answer the message. JSON only.

Input: {{user_message}}

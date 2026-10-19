---
id: emotion_classifier
version: 1.0.0
kind: skill
status: active
owner_role: design + clinical reviewer
max_tokens: 450
model_tier: small
output: runtime/schemas/emotion_result.schema.json
eval: evals/prompts/emotion_cases.json
---
Read the emotion in the user's message. Return only JSON: {"emotion": <label>, "confidence": <0 to 1>}.

Labels:
- frustrated: annoyed that something is not working or repeating
- happy: content, pleased, enjoying the moment
- confused: does not understand what is happening or what to do
- anxious: worried, nervous, fearing something might go wrong
- skeptical: doubts, distrusts, or questions whether this is right
- overwhelmed: too much at once, cannot keep up
- angry: hostile, wants it to stop
- distressed: scared, in pain, or needing someone now
- hopeful: looking forward, wishing for improvement
- confident: sure of themselves, in control
- excited: eager, thrilled, celebrating
- neutral: no clear emotion

Rules:
- Judge only this message. Never infer a condition, a diagnosis, or a long-term mood.
- If several fit, choose the most intense negative one.
- Lower confidence for short, sarcastic, or mixed messages.
- JSON only. Never answer the message.

Input: {{user_message}}

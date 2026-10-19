# ADR-005: Signals adapt behavior through a policy table

Status: active
Scope: runtime/signals

Emotion, friction and ambiguity classifiers label the turn; `adaptation.json` decides what changes.
Emotion is turn-only and never triggers a handoff. Unsure ambiguity counts as higher; unsure emotion
counts as neutral. Disclosure and fallback text are fixed copy selected by ID, never generated.
Why: inferred feelings are guesses. A guess may change how the reply sounds, but it must not
decide who is contacted or what is stored.

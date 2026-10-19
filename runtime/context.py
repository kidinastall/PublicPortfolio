"""Per-turn context passed to hooks. Synthetic, in-memory, no I/O."""
from dataclasses import dataclass, field

from runtime.copy_blocks import text
from runtime.scripts.med_schedule import Schedule


@dataclass
class Medication:
    name: str


@dataclass
class Profile:
    medications: list = field(default_factory=list)


@dataclass
class Context:
    schedule: Schedule
    profile: Profile = field(default_factory=Profile)
    prompt_version: str = "v5.2"
    repairs: int = 0
    events: list = field(default_factory=list)

    def emit(self, name, **fields):
        self.events.append({"event": name, **fields})

    def handoff(self, to, template_id):
        return {"say": text(template_id), "components": [],
                "handoff": {"to": to, "template_id": template_id},
                "meta": {"intent": "handoff", "confidence": 1.0}}

    def fallback(self, template_id):
        return {"say": text(template_id),
                "components": [{"type": "AlertBanner",
                                "props": {"severity": "info", "title": "Needs review"}}],
                "handoff": {"to": "caregiver", "template_id": "HT-020"},
                "meta": {"intent": f"fallback:{template_id}", "confidence": 1.0}}

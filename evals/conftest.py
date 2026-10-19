import pytest

from runtime.context import Context, Medication, Profile
from runtime.scripts.med_schedule import Dose, Schedule


@pytest.fixture
def ctx():
    schedule = Schedule("synthetic-001", [Dose("Medication A", "08:00"), Dose("Medication A", "20:00")])
    return Context(schedule=schedule, profile=Profile(medications=[Medication("Medication A")]))


def reply(say, components=None, handoff=None, intent="test", confidence=0.9):
    return {"say": say, "components": components or [], "handoff": handoff,
            "meta": {"intent": intent, "confidence": confidence}}

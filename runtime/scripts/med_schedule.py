"""Deterministic medication schedule. The model never computes times; it only
phrases what this module returns."""
import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Dose:
    medication: str
    time: str  # "HH:MM", 24h, patient-local


class Schedule:
    def __init__(self, patient_id, doses):
        self.patient_id = patient_id
        self.doses = list(doses)

    def times(self):
        return {d.time for d in self.doses}

    def slot_ids(self):
        """Opaque slot IDs the UI may reference; the model cannot invent a time."""
        return {self._slot(d.time) for d in self.doses}

    def slot_for(self, time):
        return self._slot(time)

    def _slot(self, time):
        h = hashlib.sha1(f"{self.patient_id}:{time}".encode()).hexdigest()[:8]
        return f"slot_{h}"

    def due(self, now_hhmm, taken):
        """Doses at or before now that are not logged as taken."""
        return [d for d in self.doses if d.time <= now_hhmm and d.time not in set(taken)]

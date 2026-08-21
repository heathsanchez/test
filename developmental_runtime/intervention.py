from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Hashable, Mapping

WorldId = Hashable
Outcome = Hashable


class InterventionKind(Enum):
    PROBE = auto()
    CONSTRUCT = auto()
    SEARCH = auto()
    RETAIN = auto()
    TERMINAL = auto()


class Terminal(Enum):
    NONE = auto()
    VERIFIED = auto()
    REFUTED = auto()
    OBSTRUCTED = auto()


@dataclass(frozen=True)
class ObligationEvidence:
    status: bool
    certificate: Any = None


@dataclass(frozen=True)
class Intervention:
    id: str
    kind: InterventionKind
    ast: Any
    cost: float = 0.0


@dataclass(frozen=True)
class TransitionRecord:
    intervention: Intervention
    effect: Any
    obligations: Mapping[str, ObligationEvidence]
    successor: Any
    terminal: Terminal = Terminal.NONE
    certificate: Any = None
    cost: float = 0.0
    provenance: Any = None

    def obligation(self, name: str) -> bool:
        ev = self.obligations.get(name)
        return bool(ev and ev.status)


REQUIRED_OBLIGATIONS: dict[InterventionKind, tuple[str, ...]] = {
    InterventionKind.PROBE: ("VERIFIED", "ADMISSIBLE", "OBSERVATION_SOUND"),
    InterventionKind.CONSTRUCT: ("VERIFIED", "ADMISSIBLE", "PRESERVE", "CHANGE_SATISFIED"),
    InterventionKind.SEARCH: ("VERIFIED", "ADMISSIBLE", "SEARCH_COVERAGE_INCREASED"),
    InterventionKind.RETAIN: ("VERIFIED", "ADMISSIBLE", "CAUSAL", "PRESERVE", "SCOPE_CERTIFIED"),
    InterventionKind.TERMINAL: ("VERIFIED", "ADMISSIBLE", "TERMINAL_CERTIFIED"),
}


def lawful(record: TransitionRecord) -> bool:
    return all(record.obligation(name) for name in REQUIRED_OBLIGATIONS[record.intervention.kind])

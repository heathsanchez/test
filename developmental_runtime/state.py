from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, FrozenSet, Hashable, Mapping

WorldId = Hashable


@dataclass(frozen=True)
class DevelopmentalState:
    problem_state: Any
    hypotheses: FrozenSet[WorldId]
    quotient: Any
    probe_language: FrozenSet[str]
    capability_language: FrozenSet[str]
    lawbook: tuple[str, ...] = ()
    obstructions: tuple[str, ...] = ()
    certificates: tuple[Any, ...] = ()
    budgets: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def evolve(self, **changes: Any) -> "DevelopmentalState":
        return replace(self, **changes)

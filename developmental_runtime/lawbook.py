from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetainedLaw:
    id: str
    payload: Any
    scope: Any
    certificates: tuple[Any, ...]
    provenance: tuple[Any, ...]


@dataclass
class Lawbook:
    laws: dict[str, RetainedLaw] = field(default_factory=dict)

    def admit(self, law: RetainedLaw) -> None:
        self.laws[law.id] = law

    def revoke(self, law_id: str) -> None:
        self.laws.pop(law_id, None)

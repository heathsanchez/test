from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Row:
    state: int
    action: int
    after: int
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    state_count: int
    action_count: int
    rows: tuple[Row,...]
    complete: bool = True

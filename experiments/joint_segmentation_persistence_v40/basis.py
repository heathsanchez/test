from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Row:
    before: tuple[int,...]
    after: tuple[int,...]
    action_before: int
    response_after: int
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    rows: tuple[Row,...]
    complete: bool = True

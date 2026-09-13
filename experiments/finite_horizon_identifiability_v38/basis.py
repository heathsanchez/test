from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Row:
    sequence: tuple[int, ...]
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    alphabet_size: int
    max_depth: int
    rows: tuple[Row, ...]
    complete: bool = True

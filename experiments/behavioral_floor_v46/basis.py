from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Trace:
    tokens: tuple[int,...]
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    alphabet_size: int
    prefix_depth: int
    max_future_depth: int
    traces: tuple[Trace,...]
    complete: bool = True

from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Sample:
    tokens: tuple[int,...]
    consequence: int

@dataclass(frozen=True)
class World:
    world_id: str
    alphabet_size: int
    consequence_alphabet_size: int
    prefix_depth: int
    max_future_depth: int
    samples: tuple[Sample,...]
    closed_histories: tuple[tuple[int,...],...]
    packet_complete: bool = True

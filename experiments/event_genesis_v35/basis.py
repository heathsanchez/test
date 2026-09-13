from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Row:
    boundary: tuple[int,...]
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    rows: tuple[Row,...]
    complete: bool = True

@dataclass(frozen=True)
class View:
    motif: tuple[int,...]
    width: int

@dataclass(frozen=True)
class Machine:
    root: int
    states: tuple[tuple[Any,...],...]

    def data(self) -> dict[str,Any]:
        return {"root": int(self.root), "states":[list(s) for s in self.states]}

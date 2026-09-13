from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Row:
    stream: tuple[int,...]
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    rows: tuple[Row,...]
    complete: bool = True

@dataclass(frozen=True)
class Machine:
    root: int
    states: tuple[tuple[Any,...], ...]

    def data(self) -> dict[str,Any]:
        return {
            "root": int(self.root),
            "states": [list(s) for s in self.states],
        }

def run_machine(machine: Machine, stream: tuple[int,...]) -> int | None:
    state=int(machine.root)
    for symbol in stream:
        row=machine.states[state]
        if row[0]=="OUT":
            continue
        if row[0]!="STEP":
            raise ValueError("unknown machine state")
        state=int(row[2] if int(symbol) else row[1])
    row=machine.states[state]
    if row[0]!="OUT":
        return None
    return int(row[1])

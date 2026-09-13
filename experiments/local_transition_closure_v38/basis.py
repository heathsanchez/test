from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Iterable, Tuple

History = Tuple[int, ...]

@dataclass(frozen=True)
class Row:
    history: History
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    rows: Tuple[Row, ...]
    complete_authority: bool = True

@dataclass(frozen=True)
class PartialMachine:
    initial: int
    outputs: Tuple[int, ...]
    transitions: Tuple[Tuple[int | None, int | None], ...]
    signatures: Tuple[Tuple[int, ...], ...]

    def data(self) -> dict:
        return {
            "initial": int(self.initial),
            "outputs": [int(x) for x in self.outputs],
            "transitions": [
                [None if z is None else int(z) for z in row]
                for row in self.transitions
            ],
            "signatures": [[int(x) for x in sig] for sig in self.signatures],
        }

def suffixes_upto(h: int) -> Tuple[History, ...]:
    out = []
    for n in range(h + 1):
        out.extend(tuple(int(x) for x in xs) for xs in product((0,1), repeat=n))
    return tuple(out)

def all_histories_upto(n: int) -> Tuple[History, ...]:
    return suffixes_upto(n)

def run_partial(machine: PartialMachine, history: Iterable[int]) -> int | None:
    q = int(machine.initial)
    for raw in history:
        b = int(raw)
        if b not in (0,1):
            raise ValueError("binary history required")
        z = machine.transitions[q][b]
        if z is None:
            return None
        q = int(z)
    return int(machine.outputs[q])

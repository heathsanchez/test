from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Iterable, Tuple

Stream = Tuple[int, ...]

@dataclass(frozen=True)
class Row:
    stream: Stream
    consequence: int | None

@dataclass(frozen=True)
class World:
    world_id: str
    rows: Tuple[Row, ...]
    complete: bool = True

@dataclass(frozen=True)
class Machine:
    initial: int
    outputs: Tuple[int, ...]
    transitions: Tuple[Tuple[int, int], ...]

    def data(self) -> dict:
        return {
            "initial": int(self.initial),
            "outputs": [int(x) for x in self.outputs],
            "transitions": [[int(a), int(b)] for a, b in self.transitions],
        }

def binary_strings_upto(n: int) -> Tuple[Stream, ...]:
    out = []
    for k in range(n + 1):
        out.extend(tuple(int(x) for x in xs) for xs in product((0, 1), repeat=k))
    return tuple(out)

def run_machine(machine: Machine, stream: Iterable[int]) -> int:
    q = int(machine.initial)
    for raw in stream:
        b = int(raw)
        if b not in (0, 1):
            raise ValueError("binary stream required")
        q = int(machine.transitions[q][b])
    return int(machine.outputs[q])

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

Signature = Tuple[int, ...]
Edge = Tuple[Signature, int, Signature]

@dataclass(frozen=True)
class PartialGraph:
    world_id: str
    initial: Signature
    states: Tuple[Signature, ...]
    warranted_edges: Tuple[Edge, ...]

    def edge_map(self) -> dict[tuple[Signature,int], Signature]:
        out = {}
        for src, sym, dst in self.warranted_edges:
            key = (tuple(src), int(sym))
            if key in out and out[key] != tuple(dst):
                raise ValueError("non-deterministic warranted edge set")
            out[key] = tuple(dst)
        return out

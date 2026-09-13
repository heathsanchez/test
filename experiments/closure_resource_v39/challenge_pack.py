from __future__ import annotations
from dataclasses import dataclass

from basis import PartialGraph, Signature

@dataclass(frozen=True)
class HiddenWorld:
    world_id: str
    graph: PartialGraph
    hidden_edges: tuple[tuple[Signature,int,Signature], ...]
    expected_displacement: int | None
    regular: bool
    preclosure: bool = False

    def hidden_map(self) -> dict[tuple[Signature,int],Signature]:
        return {
            (tuple(src),int(sym)):tuple(dst)
            for src,sym,dst in self.hidden_edges
        }

def _signature_bank(n: int, variant: int) -> tuple[Signature,...]:
    if variant == 0:
        return tuple((101 + 17*i, 307 + 11*i + i*i) for i in range(n))
    return tuple((911 - 13*i, 503 + 19*((3*i+2) % max(1,n))) for i in range(n))

def make_world(
    name: str,
    n: int,
    displacement: int,
    *,
    cycle_symbol: int,
    bit_flip: int = 0,
    label_variant: int = 0,
    misleading_displacements: tuple[int,...] | None = None,
    preclosure: bool = False,
) -> HiddenWorld:
    states = _signature_bank(n,label_variant)
    cs = int(cycle_symbol) ^ int(bit_flip)
    alt = 1-cs

    hidden = []
    for i,src in enumerate(states):
        hidden.append((src,cs,states[(i+1)%n]))
        d = displacement if misleading_displacements is None else int(misleading_displacements[i])
        hidden.append((src,alt,states[(i+d)%n]))

    warranted = []
    for i,src in enumerate(states):
        if preclosure and i == n-1:
            continue
        warranted.append((src,cs,states[(i+1)%n]))

    # Two independently verified alternate edges seed a possible regularity.
    for i in (0,1):
        src=states[i]
        d = displacement if misleading_displacements is None else int(misleading_displacements[i])
        warranted.append((src,alt,states[(i+d)%n]))

    graph = PartialGraph(
        world_id=f"{name}_bf{bit_flip}_lv{label_variant}",
        initial=states[0],
        states=states,
        warranted_edges=tuple(warranted),
    )
    return HiddenWorld(
        graph.world_id,
        graph,
        tuple(hidden),
        None if misleading_displacements is not None else int(displacement),
        misleading_displacements is None,
        preclosure,
    )

REGULAR = tuple(
    make_world("alpha",6,4,cycle_symbol=0,bit_flip=bf,label_variant=lv)
    for bf in (0,1) for lv in (0,1)
) + tuple(
    make_world("beta",7,3,cycle_symbol=1,bit_flip=bf,label_variant=lv)
    for bf in (0,1) for lv in (0,1)
)

MISLEADING = make_world(
    "gamma",
    6,
    2,
    cycle_symbol=0,
    misleading_displacements=(2,2,2,5,1,4),
)

PRECLOSURE = make_world(
    "alpha_preclosure",
    6,
    4,
    cycle_symbol=0,
    preclosure=True,
)

ALL = REGULAR + (MISLEADING, PRECLOSURE)

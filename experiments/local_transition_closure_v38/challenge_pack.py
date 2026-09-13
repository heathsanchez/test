from __future__ import annotations
from dataclasses import dataclass

from basis import Row, World, all_histories_upto

@dataclass(frozen=True)
class HiddenMachine:
    outputs: tuple[int, ...]
    transitions: tuple[tuple[int, int], ...]

RING3 = HiddenMachine(
    outputs=(0,0,1),
    transitions=(
        (0,1),  # q0
        (2,1),  # q1
        (0,2),  # q2
    ),
)

RING4 = HiddenMachine(
    outputs=(0,0,1,1),
    transitions=(
        (0,1),  # q0
        (2,1),  # q1
        (3,2),  # q2
        (0,3),  # q3
    ),
)

MACHINES = {
    "triad": RING3,
    "quartet": RING4,
}

# Canonical representatives whose h=1 consequence neighborhoods distinguish
# the hidden residual states.  These are post-freeze challenge data only.
REPS = {
    "triad": ((), (1,), (1,0)),
    "quartet": ((), (1,), (1,0), (1,0,0)),
}

# Additional target prefixes whose h=1 neighborhoods are revealed by stage.
# Stage A exposes the state identities and a directed chain.
# Stage B closes the spanning warranted cycle.
# Later stages stabilize one additional state's remaining edge at a time.
EXTRA_TARGETS = {
    "triad": {
        "A": (),
        "B": ((1,0,0),),
        "C": ((0,),),
        "D": ((1,1),),
        "E": ((1,0,1),),
    },
    "quartet": {
        "A": (),
        "B": ((1,0,0,0),),
        "C": ((0,),),
        "D": ((1,1),),
        "E": ((1,0,1),),
        "F": ((1,0,0,1),),
    },
}

STAGES = {
    "triad": ("A","B","C","D","E"),
    "quartet": ("A","B","C","D","E","F"),
}

def _flip_history(h: tuple[int,...], flip: int) -> tuple[int,...]:
    return tuple(int(b) ^ int(flip) for b in h)

def hidden_consequence(kind: str, observed_history: tuple[int,...], flip: int = 0) -> int:
    machine = MACHINES[kind]
    q = 0
    for raw in observed_history:
        b = int(raw) ^ int(flip)
        q = machine.transitions[q][b]
    return int(machine.outputs[q])

def _neighborhood_h1(prefix: tuple[int,...]) -> set[tuple[int,...]]:
    return {
        prefix,
        prefix + (0,),
        prefix + (1,),
    }

def canonical_authority(kind: str, stage: str) -> set[tuple[int,...]]:
    auth: set[tuple[int,...]] = set()

    # State-identity support.
    for rep in REPS[kind]:
        auth |= _neighborhood_h1(rep)

    # Add all stage targets up through the requested stage.
    for s in STAGES[kind]:
        if s == "A":
            if stage == "A":
                break
            continue
        for p in EXTRA_TARGETS[kind][s]:
            auth |= _neighborhood_h1(p)
        if s == stage:
            break

    # Prefix closure is explicit authority, not inferred by the kernel.
    closed = set(auth)
    for h in list(auth):
        for k in range(len(h)+1):
            closed.add(h[:k])
    return closed

def make_world(kind: str, stage: str, *, flip: int = 0) -> World:
    canonical = canonical_authority(kind, stage)
    observed = sorted(
        {_flip_history(h, flip) for h in canonical},
        key=lambda h: (len(h), h),
    )
    rows = tuple(
        Row(h, hidden_consequence(kind, h, flip))
        for h in observed
    )
    return World(f"{kind}_flip{flip}_stage{stage}", rows, True)

WORLDS = tuple(
    make_world(kind, stage, flip=flip)
    for kind in STAGES
    for stage in STAGES[kind]
    for flip in (0,1)
)

def corrupt_world() -> World:
    base = make_world("triad","B",flip=0)
    rows = list(base.rows)
    # Remove a required parent while retaining descendants.
    rows = [r for r in rows if tuple(r.history) != (1,0,0)]
    return World("corrupt_prefix_authority", tuple(rows), True)

CORRUPT = corrupt_world()

def heldout_rows(kind: str, *, flip: int = 0, max_depth: int = 8) -> tuple[Row,...]:
    return tuple(
        Row(h, hidden_consequence(kind, h, flip))
        for h in all_histories_upto(max_depth)
    )

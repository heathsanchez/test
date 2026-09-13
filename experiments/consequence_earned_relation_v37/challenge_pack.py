from __future__ import annotations
from itertools import product
from basis import Row, World

N = 6

def normalize_edge(i: int, j: int) -> tuple[int, int]:
    return (i, j) if i < j else (j, i)

HIDDEN_NEIGHBOR_RELATION = tuple(sorted({
    normalize_edge(i, (i + 1) % N) for i in range(N)
}))

HIDDEN_AMBIGUOUS_RELATION = tuple(
    (i, i + 1) for i in range(N - 1)
)

def edge_count(edges: tuple[tuple[int, int], ...], x: tuple[int, ...]) -> int:
    return sum(int(x[i]) * int(x[j]) for i, j in edges)

def rotations(s: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(s[i:] + s[:i] for i in range(len(s)))

def anchored_reverse(s: tuple[int, ...]) -> tuple[int, ...]:
    return (s[0],) + tuple(reversed(s[1:]))

def dihedral_rep(s: tuple[int, ...]) -> tuple[int, ...]:
    rev = tuple(reversed(s))
    return min(rotations(s) + rotations(rev))

def cyclic_rep(s: tuple[int, ...]) -> tuple[int, ...]:
    return min(rotations(s))

def anchored_rep(s: tuple[int, ...]) -> tuple[int, ...]:
    return min(s, anchored_reverse(s))

def code(bits: tuple[int, ...]) -> int:
    out = 0
    for b in bits:
        out = (out << 1) | int(b)
    return out

def make_world(
    world_id: str,
    fn,
    *,
    relabel: bool = False,
    incomplete: bool = False,
) -> World:
    configs = list(product((0, 1), repeat=N))
    if incomplete:
        configs = configs[:-1]
    rows = []
    for x in configs:
        y = int(fn(tuple(x)))
        if relabel:
            y = 101 + 17 * y
        rows.append(Row(tuple(x), y))
    return World(world_id, tuple(rows), not incomplete)

CONSTANT = make_world("constant", lambda x: 0)

NEIGHBOR = make_world(
    "neighbor",
    lambda x: edge_count(HIDDEN_NEIGHBOR_RELATION, x),
)

NEIGHBOR_RELABELLED = make_world(
    "neighbor_relabelled",
    lambda x: edge_count(HIDDEN_NEIGHBOR_RELATION, x),
    relabel=True,
)

AMBIGUOUS = make_world(
    "ambiguous",
    lambda x: edge_count(HIDDEN_AMBIGUOUS_RELATION, x),
)

FRAME_FAMILY = {
    "g12": make_world("g12", lambda x: code(dihedral_rep(x))),
    "g6": make_world("g6", lambda x: code(cyclic_rep(x))),
    "g2": make_world("g2", lambda x: code(anchored_rep(x))),
    "g1": make_world("g1", lambda x: code(x)),
}

CANONICAL_ONE = make_world(
    "canonical_one",
    lambda x: int(dihedral_rep(x)[0]),
)

LOCAL_TWO = make_world(
    "local_two",
    lambda x: code(tuple(x[:2])),
)

LOCAL_THREE = make_world(
    "local_three",
    lambda x: code(tuple(x[:3])),
)

INCOMPLETE = make_world(
    "incomplete",
    lambda x: edge_count(HIDDEN_NEIGHBOR_RELATION, x),
    incomplete=True,
)

def rotation_permutation(k: int) -> tuple[int, ...]:
    return tuple((i + k) % N for i in range(N))

def reflection_permutation(k: int) -> tuple[int, ...]:
    return tuple((k - i) % N for i in range(N))

EXPECTED_GROUP_12 = tuple(sorted({
    rotation_permutation(k) for k in range(N)
} | {
    reflection_permutation(k) for k in range(N)
}))

EXPECTED_GROUP_6 = tuple(sorted({
    rotation_permutation(k) for k in range(N)
}))

EXPECTED_GROUP_2 = tuple(sorted({
    tuple(range(N)),
    reflection_permutation(0),
}))

EXPECTED_GROUP_1 = (tuple(range(N)),)

from __future__ import annotations
from itertools import product
from basis import Row, World

ALPHABET_SIZE = 2
DEPTHS = tuple(range(0, 9))

def sequences(max_depth: int) -> tuple[tuple[int, ...], ...]:
    out = []
    for n in range(max_depth + 1):
        out.extend(tuple(int(x) for x in xs) for xs in product(range(ALPHABET_SIZE), repeat=n))
    return tuple(out)

def make_world(world_id: str, max_depth: int, fn, *, incomplete: bool = False) -> World:
    seqs = list(sequences(max_depth))
    if incomplete:
        seqs = seqs[:-1]
    rows = tuple(Row(seq, int(fn(seq))) for seq in seqs)
    return World(world_id, ALPHABET_SIZE, max_depth, rows, not incomplete)

def zero_fn(seq: tuple[int, ...]) -> int:
    return 0

def separator_sequence(depth: int) -> tuple[int, ...]:
    return tuple(1 for _ in range(depth + 1))

def delayed_fn(depth: int):
    witness = separator_sequence(depth)
    def fn(seq: tuple[int, ...]) -> int:
        return int(tuple(seq) == witness)
    return fn

PREFIX_PAIRS = {
    depth: (
        make_world(f"left_prefix_{depth}", depth, zero_fn),
        make_world(f"right_prefix_{depth}", depth, delayed_fn(depth)),
    )
    for depth in DEPTHS
}

EXTENDED_PAIRS = {
    depth: (
        make_world(f"left_extended_{depth}", depth + 1, zero_fn),
        make_world(f"right_extended_{depth}", depth + 1, delayed_fn(depth)),
    )
    for depth in DEPTHS
}

IDENTICAL_PAIR = (
    make_world("identical_left", max(DEPTHS) + 1, zero_fn),
    make_world("identical_right", max(DEPTHS) + 1, zero_fn),
)

INCOMPLETE = make_world("incomplete", 4, zero_fn, incomplete=True)
COMPLETE_FOR_INCOMPLETE = make_world("complete_for_incomplete", 4, zero_fn)

from __future__ import annotations
from typing import Callable

from basis import Row, World, binary_strings_upto

TRAIN_MAX = 6
TEST_MAX = 10

def _contains(s: tuple[int, ...], pattern: tuple[int, ...]) -> bool:
    m = len(pattern)
    return any(s[i:i+m] == pattern for i in range(len(s)-m+1))

def _variable_event(s: tuple[int, ...]) -> int:
    state = 0
    for b in s:
        if state == 0:
            if b == 0:
                state = 1
        elif state == 1:
            if b == 1:
                state = 2
        elif state == 2:
            if b == 0:
                return 1
    return 0

SEMANTICS: dict[str, Callable[[tuple[int, ...]], int]] = {
    "constant": lambda s: 0,
    "trigger": lambda s: int(any(s)),
    "parity": lambda s: int(sum(s) % 2),
    "motif01": lambda s: int(_contains(s, (0, 1))),
    "motif101": lambda s: int(_contains(s, (1, 0, 1))),
    "variable_duration": _variable_event,
}

EXPECTED_STATES = {
    "constant": 1,
    "trigger": 2,
    "parity": 2,
    "motif01": 3,
    "motif101": 4,
    "variable_duration": 4,
}

def _observed(s: tuple[int, ...], flip: int) -> tuple[int, ...]:
    return tuple(int(b) ^ int(flip) for b in s)

def make_world(kind: str, *, flip: int = 0, max_len: int = TRAIN_MAX, incomplete: bool = False) -> World:
    fn = SEMANTICS[kind]
    rows = []
    for s in binary_strings_upto(max_len):
        obs = _observed(s, flip)
        y = None if incomplete else int(fn(s))
        rows.append(Row(obs, y))
    return World(f"{kind}_flip{flip}_L{max_len}", tuple(rows), not incomplete)

TRAIN = tuple(make_world(kind, flip=flip) for kind in SEMANTICS for flip in (0, 1))
INCOMPLETE = make_world("trigger", incomplete=True)

def heldout_rows(kind: str, *, flip: int = 0, max_len: int = TEST_MAX) -> tuple[Row, ...]:
    fn = SEMANTICS[kind]
    return tuple(Row(_observed(s, flip), int(fn(s))) for s in binary_strings_upto(max_len))

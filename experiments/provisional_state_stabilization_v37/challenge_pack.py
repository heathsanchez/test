from __future__ import annotations
from typing import Callable

from basis import Bits, Row, World, encode_tokens, token_sequences

CODEBOOKS: dict[str, tuple[Bits, Bits]] = {
    "p2": ((0,), (1,1,0)),
    "p3": ((0,0,1), (1,)),
    "p4": ((0,), (1,1,1)),
    "cycle": ((0,1), (1,)),
}

def _contains(seq: tuple[int, ...], pat: tuple[int, ...]) -> bool:
    m = len(pat)
    return any(seq[i:i+m] == pat for i in range(len(seq)-m+1))

SEMANTICS: dict[str, Callable[[tuple[int, ...]], int]] = {
    "p2": lambda s: int(_contains(s, (0,1))),
    "p3": lambda s: int(_contains(s, (1,0,1))),
    "p4": lambda s: int(_contains(s, (1,0,1,1))),
    "cycle": lambda s: int(sum(1 for x in s if x == 1) % 2),
}

EXPECTED = {
    "p2": {"states": 3, "horizon": 1},
    "p3": {"states": 4, "horizon": 2},
    "p4": {"states": 5, "horizon": 3},
    "cycle": {"states": 2, "horizon": 0},
}

STAGES = {
    "p2": (4,),
    "p3": (5,6),
    "p4": (7,8),
    "cycle": (3,),
}

def flip_word(word: Bits, flip: int) -> Bits:
    return tuple(int(b) ^ int(flip) for b in word)

def codebook_for(kind: str, flip: int = 0) -> tuple[Bits, Bits]:
    return tuple(flip_word(w, flip) for w in CODEBOOKS[kind])

def make_world(
    kind: str,
    depth: int,
    *,
    flip: int = 0,
    incomplete: bool = False,
) -> World:
    cb = codebook_for(kind, flip)
    fn = SEMANTICS[kind]
    seqs = list(token_sequences(2, depth))
    if incomplete:
        seqs = seqs[:-1]
    rows = tuple(
        Row(encode_tokens(seq, cb), int(fn(seq)))
        for seq in seqs
    )
    return World(
        f"{kind}_flip{flip}_D{depth}",
        rows,
        not incomplete,
    )

WORLDS = tuple(
    make_world(kind, depth, flip=flip)
    for kind, depths in STAGES.items()
    for depth in depths
    for flip in (0,1)
)

INCOMPLETE = make_world("p3", 5, incomplete=True)

def heldout_rows(
    kind: str,
    max_depth: int,
    *,
    flip: int = 0,
) -> tuple[Row, ...]:
    cb = codebook_for(kind, flip)
    fn = SEMANTICS[kind]
    return tuple(
        Row(encode_tokens(seq, cb), int(fn(seq)))
        for seq in token_sequences(2, max_depth)
    )

def hidden_codebook_strings(kind: str, flip: int = 0) -> set[str]:
    return {
        "".join(str(int(b)) for b in word)
        for word in codebook_for(kind, flip)
    }

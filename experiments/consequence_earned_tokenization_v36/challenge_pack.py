from __future__ import annotations
from typing import Callable

from basis import Bits, Row, World, encode_tokens, token_sequences

TRAIN_TOKENS = 5
TEST_TOKENS = 8

BASE_CODEBOOKS: dict[str, tuple[Bits, Bits]] = {
    "constant": ((0,), (1,0)),
    "last": ((0,0), (1,)),
    "parity": ((0,1), (1,)),
    "relation2": ((0,), (1,1,0)),
    "relation3": ((0,0,1), (1,)),
    "mod3": ((0,), (1,1,1)),
}

def _contains(seq: tuple[int, ...], pat: tuple[int, ...]) -> bool:
    m = len(pat)
    return any(seq[i:i+m] == pat for i in range(len(seq)-m+1))

SEMANTICS: dict[str, Callable[[tuple[int, ...]], int]] = {
    "constant": lambda s: 0,
    "last": lambda s: int(s[-1]) if s else 0,
    "parity": lambda s: int(sum(1 for x in s if x == 1) % 2),
    "relation2": lambda s: int(_contains(s, (0,1))),
    "relation3": lambda s: int(_contains(s, (1,0,1))),
    "mod3": lambda s: int(sum(1 for x in s if x == 1) % 3),
}

EXPECTED_STATES = {
    "constant": 1,
    "last": 2,
    "parity": 2,
    "relation2": 3,
    "relation3": 4,
    "mod3": 3,
}

def flip_word(word: Bits, flip: int) -> Bits:
    return tuple(int(b) ^ int(flip) for b in word)

def codebook_for(kind: str, flip: int = 0) -> tuple[Bits, Bits]:
    return tuple(flip_word(w, flip) for w in BASE_CODEBOOKS[kind])

def make_world(kind: str, *, flip: int = 0, max_tokens: int = TRAIN_TOKENS, incomplete: bool = False) -> World:
    cb = codebook_for(kind, flip)
    fn = SEMANTICS[kind]
    rows = []
    seqs = token_sequences(2, max_tokens)
    if incomplete:
        seqs = seqs[:-1]
    for seq in seqs:
        raw = encode_tokens(seq, cb)
        rows.append(Row(raw, int(fn(seq))))
    return World(f"{kind}_flip{flip}_T{max_tokens}", tuple(rows), not incomplete)

TRAIN = tuple(make_world(kind, flip=flip) for kind in SEMANTICS for flip in (0,1))
INCOMPLETE = make_world("relation2", incomplete=True)

def heldout_rows(kind: str, *, flip: int = 0, max_tokens: int = TEST_TOKENS) -> tuple[Row, ...]:
    cb = codebook_for(kind, flip)
    fn = SEMANTICS[kind]
    return tuple(
        Row(encode_tokens(seq, cb), int(fn(seq)))
        for seq in token_sequences(2, max_tokens)
    )

def hidden_codebook_strings(kind: str, flip: int = 0) -> set[str]:
    return {"".join(str(int(b)) for b in w) for w in codebook_for(kind, flip)}

def boundary_positions(kind: str, seq: tuple[int, ...], flip: int = 0) -> tuple[int, ...]:
    cb = codebook_for(kind, flip)
    pos = 0
    out = []
    for t in seq[:-1]:
        pos += len(cb[int(t)])
        out.append(pos)
    return tuple(out)

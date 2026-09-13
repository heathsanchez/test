from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Iterable, Tuple

Bits = Tuple[int, ...]
Tokens = Tuple[int, ...]

@dataclass(frozen=True)
class Row:
    raw: Bits
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
    transitions: Tuple[Tuple[int, ...], ...]

    def data(self) -> dict:
        return {
            "initial": int(self.initial),
            "outputs": [int(x) for x in self.outputs],
            "transitions": [[int(z) for z in t] for t in self.transitions],
        }

def binary_words(min_len: int, max_len: int) -> Tuple[Bits, ...]:
    out = []
    for n in range(min_len, max_len + 1):
        out.extend(tuple(int(x) for x in xs) for xs in product((0, 1), repeat=n))
    return tuple(out)

def token_sequences(alphabet_size: int, max_len: int) -> Tuple[Tokens, ...]:
    out = []
    for n in range(max_len + 1):
        out.extend(tuple(int(x) for x in xs) for xs in product(range(alphabet_size), repeat=n))
    return tuple(out)

def is_prefix_free(codebook: Tuple[Bits, ...]) -> bool:
    for i, a in enumerate(codebook):
        for j, b in enumerate(codebook):
            if i == j:
                continue
            if len(a) <= len(b) and tuple(b[:len(a)]) == tuple(a):
                return False
    return True

def parse_prefix_free(raw: Bits, codebook: Tuple[Bits, ...]) -> Tokens | None:
    pos = 0
    out = []
    while pos < len(raw):
        matches = []
        for i, word in enumerate(codebook):
            if tuple(raw[pos:pos+len(word)]) == tuple(word):
                matches.append((i, word))
        if len(matches) != 1:
            return None
        i, word = matches[0]
        out.append(int(i))
        pos += len(word)
    return tuple(out)

def encode_tokens(tokens: Iterable[int], codebook: Tuple[Bits, ...]) -> Bits:
    out = []
    for t in tokens:
        out.extend(codebook[int(t)])
    return tuple(int(x) for x in out)

def run_machine(machine: Machine, tokens: Iterable[int]) -> int:
    q = int(machine.initial)
    for raw in tokens:
        t = int(raw)
        if t < 0 or t >= len(machine.transitions[q]):
            raise ValueError("token outside machine alphabet")
        q = int(machine.transitions[q][t])
    return int(machine.outputs[q])

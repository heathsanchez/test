#!/usr/bin/env python3
"""Frozen V15 positional-schema substrate."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Sequence, Tuple


Token = str
Pattern = Tuple[int, ...]


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerifiedLiteral:
    tokens: Tuple[Token, ...]
    provenance: Tuple[str, ...]
    verified: bool = True
    interface: str = "opaque_lower_token_sequence"

    def authoritative(self) -> bool:
        return self.verified and bool(self.tokens) and bool(self.provenance)


def canonicalize_pattern(pattern: Sequence[int]) -> Pattern:
    mapping = {}
    next_id = 0
    out = []
    for x in pattern:
        x = int(x)
        if x not in mapping:
            mapping[x] = next_id
            next_id += 1
        out.append(mapping[x])
    return tuple(out)


def generate_partitions(n: int) -> Tuple[Pattern, ...]:
    n = int(n)
    if n <= 0:
        return tuple()
    out = []

    def rec(prefix, max_seen):
        if len(prefix) == n:
            out.append(tuple(prefix))
            return
        for x in range(max_seen + 2):
            if not prefix and x != 0:
                continue
            prefix.append(x)
            rec(prefix, max(max_seen, x))
            prefix.pop()

    rec([], -1)
    # rec above can overgenerate non-canonical sequences; filter exact RGS.
    uniq = []
    seen = set()
    for p in out:
        c = canonicalize_pattern(p)
        if c == p and c not in seen:
            seen.add(c)
            uniq.append(c)
    uniq.sort(key=lambda p: (len(set(p)), p))
    return tuple(uniq)


def pattern_fits(pattern: Pattern, literal: VerifiedLiteral) -> bool:
    if len(pattern) != len(literal.tokens):
        return False
    for i in range(len(pattern)):
        for j in range(i + 1, len(pattern)):
            if pattern[i] == pattern[j] and literal.tokens[i] != literal.tokens[j]:
                return False
    return True


def pattern_fits_all(pattern: Pattern, literals: Iterable[VerifiedLiteral]) -> bool:
    return all(pattern_fits(pattern, lit) for lit in literals)


def is_refinement(new: Pattern, old: Pattern) -> bool:
    if len(new) != len(old):
        return False
    # Splitting only: new equality may only occur where old already had equality.
    for i in range(len(new)):
        for j in range(i + 1, len(new)):
            if new[i] == new[j] and old[i] != old[j]:
                return False
    return True


def parameter_count(pattern: Pattern) -> int:
    return len(set(pattern))


def bindings_for(pattern: Pattern, literal: VerifiedLiteral):
    if not pattern_fits(pattern, literal):
        return None
    b = {}
    for pos, var in enumerate(pattern):
        b.setdefault(var, literal.tokens[pos])
        if b[var] != literal.tokens[pos]:
            return None
    return tuple(b[i] for i in range(parameter_count(pattern)))


def instantiate(pattern: Pattern, bindings: Sequence[Token]) -> Tuple[Token, ...]:
    if len(bindings) < parameter_count(pattern):
        raise ValueError("insufficient bindings")
    return tuple(bindings[var] for var in pattern)


def schema_id(pattern: Pattern) -> str:
    return "schema_" + digest_json({"pattern": list(pattern)})[:16]

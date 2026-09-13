#!/usr/bin/env python3
"""Frozen V14 substrate for consequence-gated straight-line grammar genesis."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, Mapping, Sequence, Tuple


Primitive = int
Token = str
Episode = Tuple[Token, ...]


def digest_json(x: Any) -> str:
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class VerifiedPhraseAtom:
    atom_id: str
    expansion: Tuple[Primitive, ...]
    provenance: Tuple[str, ...]
    verified: bool = True
    interface: str = "anonymous_action_stream"

    def authoritative(self) -> bool:
        return (
            bool(self.atom_id)
            and bool(self.expansion)
            and self.verified
            and len(set(self.provenance)) >= 2
        )

    def data(self) -> Any:
        return {
            "atom_id": self.atom_id,
            "expansion": list(self.expansion),
            "provenance": list(self.provenance),
            "verified": self.verified,
            "interface": self.interface,
        }


@dataclass(frozen=True)
class GrammarCorpus:
    atoms: Mapping[str, VerifiedPhraseAtom]
    episodes: Tuple[Episode, ...]
    complete_authority: bool
    corpus_id: str = ""

    def __post_init__(self) -> None:
        if not self.episodes:
            raise ValueError("corpus must contain at least one episode")
        for episode in self.episodes:
            if not episode:
                raise ValueError("episodes must be nonempty")
            for token in episode:
                if token not in self.atoms:
                    raise ValueError(f"unknown phrase atom: {token}")

    def authoritative(self) -> bool:
        return (
            self.complete_authority
            and all(atom.authoritative() for atom in self.atoms.values())
        )

    def primitive_expansion(self, episode: Sequence[Token]) -> Tuple[Primitive, ...]:
        out = []
        for token in episode:
            out.extend(self.atoms[token].expansion)
        return tuple(out)

    def source_expansions(self) -> Tuple[Tuple[Primitive, ...], ...]:
        return tuple(self.primitive_expansion(ep) for ep in self.episodes)

    def interface_key(self) -> Tuple[str, ...]:
        return tuple(sorted(set(atom.interface for atom in self.atoms.values())))


def anonymous_rule_id(rhs: Sequence[str]) -> str:
    return "g_" + digest_json({"rhs": list(rhs)})[:16]

#!/usr/bin/env python3
"""Protected-future quotient primitives for the Collatz Crystal compiler.

These functions are domain-independent graph machinery.  They do not claim
that a finite graph is a complete Collatz residual presentation.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Hashable, Iterable, Mapping, Optional, Set, Tuple

Node = Hashable


def _partition(groups: Mapping[Node, int]) -> Set[frozenset]:
    out: Dict[int, Set[Node]] = defaultdict(set)
    for node, cls in groups.items():
        out[cls].add(node)
    return {frozenset(v) for v in out.values()}


def refine_future_quotient(
    nodes: Iterable[Node],
    succ: Mapping[Node, Set[Node]],
    exits: Set[Node],
) -> Tuple[Dict[Node, int], Set[int], Dict[int, Set[int]], Set[int]]:
    """Coarsest stable quotient by exit flag and successor-class set."""
    ordered = sorted(set(nodes), key=repr)
    classes = {n: int(n in exits) for n in ordered}

    while True:
        sig = {
            n: (n in exits, tuple(sorted({classes[t] for t in succ.get(n, set())})))
            for n in ordered
        }
        unique = {
            s: i for i, s in enumerate(sorted(set(sig.values()), key=repr))
        }
        new = {n: unique[sig[n]] for n in ordered}
        if _partition(new) == _partition(classes):
            classes = new
            break
        classes = new

    qnodes = set(classes.values())
    qsucc = {q: set() for q in qnodes}
    qexits: Set[int] = set()
    for n in ordered:
        q = classes[n]
        if n in exits:
            qexits.add(q)
        for t in succ.get(n, set()):
            qsucc[q].add(classes[t])
    return classes, qnodes, qsucc, qexits


def greatest_kernel(
    nodes: Iterable[Node],
    succ: Mapping[Node, Set[Node]],
) -> Set[Node]:
    """Greatest post-fixed subset: repeatedly remove nodes with no live successor."""
    live = set(nodes)
    while True:
        dead = {n for n in live if not (set(succ.get(n, set())) & live)}
        if not dead:
            return live
        live -= dead


def rank_if_acyclic(
    nodes: Iterable[Node],
    succ: Mapping[Node, Set[Node]],
) -> Optional[Dict[Node, int]]:
    """Return natural height rank decreasing on every internal edge, else None."""
    remaining = set(nodes)
    rank: Dict[Node, int] = {}
    level = 0
    while remaining:
        sinks = {
            n for n in remaining
            if not (set(succ.get(n, set())) & remaining)
        }
        if not sinks:
            return None
        for n in sorted(sinks, key=repr):
            rank[n] = level
        remaining -= sinks
        level += 1

    for s in rank:
        for t in set(succ.get(s, set())) & set(rank):
            if not rank[t] < rank[s]:
                raise AssertionError((s, t, rank[s], rank[t]))
    return rank

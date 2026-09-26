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


def _find_cycle(nodes, succ):
    live=set(nodes)
    seen=set()
    stack=[]
    on=set()
    def dfs(v):
        seen.add(v); stack.append(v); on.add(v)
        for w in sorted(set(succ.get(v,set())) & live, key=repr):
            if w not in seen:
                got=dfs(w)
                if got: return got
            elif w in on:
                i=stack.index(w)
                return stack[i:]+[w]
        stack.pop(); on.remove(v)
        return None
    for v in sorted(live,key=repr):
        if v not in seen:
            got=dfs(v)
            if got: return got
    return []


def compile_with_separators(occurrences, base_fields, separator_bank):
    """Compile an observed protected-future graph without inventing identity.

    A separator is admitted only when adding it changes the stable future
    partition.  Empty-kernel results are bounded evidence unless separate
    universal normalization/progress authorities are supplied elsewhere.
    """
    rows={r["id"]:dict(r) for r in occurrences}
    ids=set(rows)
    raw_succ={i:set(rows[i].get("next",())) & ids for i in ids}
    exits={i for i in ids if rows[i].get("exit",False)}
    fields=list(base_fields)
    admitted=[]

    def graph(fs):
        # Initial semantic labels are the selected exact fields plus exit flag.
        label={i:(tuple(rows[i].get(k) for k in fs), i in exits) for i in ids}
        # Refine labels by protected successor futures to a fixed point.
        while True:
            sig={i:(label[i], tuple(sorted({label[t] for t in raw_succ[i]},key=repr)))
                 for i in ids}
            uniq={s:n for n,s in enumerate(sorted(set(sig.values()),key=repr))}
            new={i:uniq[sig[i]] for i in ids}
            # Normalize old labels to partition IDs for a partition comparison.
            olduniq={s:n for n,s in enumerate(sorted(set(label.values()),key=repr))}
            old={i:olduniq[label[i]] for i in ids}
            if _partition(new)==_partition(old):
                classes=new
                break
            label=new
        qnodes=set(classes.values())
        qsucc={q:set() for q in qnodes}
        qexit=set()
        for i in ids:
            q=classes[i]
            if i in exits: qexit.add(q)
            for t in raw_succ[i]: qsucc[q].add(classes[t])
        residual=qnodes-qexit
        rsucc={q:(qsucc[q] & residual) for q in residual}
        return classes,residual,rsucc

    classes,residual,rsucc=graph(fields)
    kernel=greatest_kernel(residual,rsucc)
    for sep in separator_bank:
        trial_classes,trial_residual,trial_succ=graph(fields+[sep])
        if _partition(trial_classes) != _partition(classes):
            fields.append(sep); admitted.append(sep)
            classes,residual,rsucc=trial_classes,trial_residual,trial_succ
            kernel=greatest_kernel(residual,rsucc)
            if not kernel:
                break

    if kernel:
        cycle=_find_cycle(kernel,rsucc)
        return {
            "status":"EXACT_RECURRENT_OBSTRUCTION",
            "admitted_separators":admitted,
            "kernel":sorted(kernel),
            "rank":None,
            "obstruction":{"cycle":cycle},
        }
    rank=rank_if_acyclic(residual,rsucc)
    return {
        "status":"BOUNDED_EMPTY_KERNEL",
        "admitted_separators":admitted,
        "kernel":[],
        "rank":rank,
        "obstruction":None,
    }

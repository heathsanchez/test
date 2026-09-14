#!/usr/bin/env python3
"""
MDA Genesis/Solvent Convergence Test v1

Purpose:
  Freeze one behavioral warrant W.
  Approach the minimally sufficient present from both directions:

    GENESIS: start with no distinctions and earn structure from consequence.
    SOLVENT: start maximally overcomplete and search the full partition lattice
             for the jointly minimal lawful + sufficient contraction.

The construction deliberately contains 8 atoms: two structural copies of each
of 4 hidden behavioral states. The copy index is behaviorally irrelevant, but
transitions preserve it. This makes one-at-a-time pruning fail: no 7-, 6-, or
5-block lawful+sufficient quotient exists, even though a 4-block quotient does.
So SOLVENT must reason over configurations, not individual deletions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import product
from typing import Dict, FrozenSet, Iterable, Iterator, List, Sequence, Tuple

State = int
Copy = int
Atom = Tuple[State, Copy]
Block = FrozenSet[Atom]
Partition = Tuple[Block, ...]

HIDDEN = {
    0: {0: (0, 0), 1: (1, 1)},
    1: {0: (2, 0), 1: (3, 1)},
    2: {0: (0, 1), 1: (1, 0)},
    3: {0: (2, 1), 1: (3, 0)},
}

ATOMS: Tuple[Atom, ...] = tuple((s, c) for s in range(4) for c in range(2))
ALPHABET = (0, 1)
WARRANT_HORIZON = 2


def trace(atom: Atom, word: Sequence[int]) -> Tuple[int, ...]:
    s, _copy = atom
    outs: List[int] = []
    for a in word:
        s, o = HIDDEN[s][a]
        outs.append(o)
    return tuple(outs)


def future_signature(atom: Atom, k: int) -> Tuple[Tuple[int, ...], ...]:
    if k == 0:
        return ((),)
    return tuple(
        trace(atom, word)
        for word in product(ALPHABET, repeat=k)
    )


FROZEN_WARRANT: Dict[Atom, Tuple[Tuple[int, ...], ...]] = {
    a: future_signature(a, WARRANT_HORIZON) for a in ATOMS
}


def canonical(part: Partition) -> Tuple[Tuple[Atom, ...], ...]:
    return tuple(sorted((tuple(sorted(b)) for b in part), key=lambda b: b))


def block_index(part: Partition) -> Dict[Atom, int]:
    return {a: i for i, block in enumerate(part) for a in block}


def warrant_sufficient(part: Partition) -> bool:
    """Replay frozen consequence: merged atoms must agree on every frozen test."""
    return all(len({FROZEN_WARRANT[a] for a in block}) == 1 for block in part)


def right_congruent(part: Partition) -> bool:
    """A quotient is lawful only if each block has a well-defined next block."""
    where = block_index(part)
    for block in part:
        for inp in ALPHABET:
            targets = set()
            for s, c in block:
                ns, _ = HIDDEN[s][inp]
                targets.add(where[(ns, c)])
            if len(targets) > 1:
                return False
    return True


def lawful_and_sufficient(part: Partition) -> bool:
    return warrant_sufficient(part) and right_congruent(part)


def partition_from_horizon(k: int) -> Partition:
    groups: Dict[Tuple[Tuple[int, ...], ...], List[Atom]] = defaultdict(list)
    for atom in ATOMS:
        groups[future_signature(atom, k)].append(atom)
    return tuple(frozenset(v) for _, v in sorted(groups.items(), key=lambda kv: repr(kv[0])))


def genesis(max_k: int = 4):
    """
    Grow from below: k=0 starts with all atoms equivalent.
    Increase observational resolution only until the first lawful+sufficient
    partition whose next horizon does not split it further.
    """
    attempts = []
    for k in range(max_k + 1):
        part = partition_from_horizon(k)
        sufficient = warrant_sufficient(part)
        congruent = right_congruent(part)
        next_same = False
        if k < max_k:
            next_same = canonical(part) == canonical(partition_from_horizon(k + 1))
        attempts.append({
            "k": k,
            "blocks": len(part),
            "sufficient": sufficient,
            "right_congruent": congruent,
            "stable_next": next_same,
        })
        if sufficient and congruent and next_same:
            return part, attempts
    raise RuntimeError("GENESIS did not reach a stable lawful+sufficient present")


def set_partitions(items: Sequence[Atom]) -> Iterator[Partition]:
    """Generate each set partition exactly once (Bell(8)=4140 here)."""
    blocks: List[List[Atom]] = []

    def rec(i: int) -> Iterator[Partition]:
        if i == len(items):
            yield tuple(frozenset(b) for b in blocks)
            return

        x = items[i]

        for j in range(len(blocks)):
            blocks[j].append(x)
            yield from rec(i + 1)
            blocks[j].pop()

        blocks.append([x])
        yield from rec(i + 1)
        blocks.pop()

    yield from rec(0)


def solvent():
    """
    Dissolve from above globally, not greedily.

    Start conceptually from the 8-singleton overcomplete present, enumerate the
    full partition lattice, retain only lawful+sufficient contractions, and
    select the minimum block count. This can cross valleys where no individual
    merge is valid but a coordinated set of merges is.
    """
    valid: List[Partition] = []
    counts = Counter()
    total = 0

    for part in set_partitions(ATOMS):
        total += 1
        if lawful_and_sufficient(part):
            valid.append(part)
            counts[len(part)] += 1

    if not valid:
        raise RuntimeError("SOLVENT found no lawful+sufficient present")

    min_blocks = min(len(p) for p in valid)
    minima = [p for p in valid if len(p) == min_blocks]
    minima.sort(key=canonical)
    return minima[0], {
        "partitions_examined": total,
        "valid_by_block_count": dict(sorted(counts.items())),
        "minimum_block_count": min_blocks,
        "n_minima": len(minima),
    }


def greedy_one_merge_exists(part: Partition) -> bool:
    """Can one pair of current blocks be merged while preserving the warrant?"""
    n = len(part)
    for i in range(n):
        for j in range(i + 1, n):
            merged = [b for k, b in enumerate(part) if k not in (i, j)]
            merged.append(part[i] | part[j])
            candidate = tuple(merged)
            if lawful_and_sufficient(candidate):
                return True
    return False


def force_underfit_from_minimum(minimum: Partition) -> Partition:
    """Collapse two genuinely distinct behavioral blocks to make a 3-block control."""
    blocks = list(minimum)
    assert len(blocks) == 4
    return tuple([blocks[0] | blocks[1]] + blocks[2:])


def run():
    checks = []

    def chk(name: str, cond: bool, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 78)
    print("MDA GENESIS/SOLVENT CONVERGENCE TEST v1")
    print("=" * 78)
    print(f"atoms={len(ATOMS)}  frozen_warrant_horizon={WARRANT_HORIZON}")

    # A. Freeze the warrant before either search direction.
    print("\n--- A. Frozen warrant ---")
    distinct_warrant_classes = len(set(FROZEN_WARRANT.values()))
    chk("A1 warrant freezes four behavioral classes",
        distinct_warrant_classes == 4,
        f"classes={distinct_warrant_classes}")
    chk("A2 copy index is invisible to the warrant",
        all(FROZEN_WARRANT[(s, 0)] == FROZEN_WARRANT[(s, 1)] for s in range(4)))

    # B. GENESIS: approach from too little structure.
    print("\n--- B. GENESIS from below ---")
    g, attempts = genesis()
    for row in attempts:
        print("   ", row)
    chk("B1 GENESIS begins underfit at k=0",
        attempts[0]["blocks"] == 1 and not attempts[0]["sufficient"])
    chk("B2 k=1 remains inadequate",
        attempts[1]["blocks"] == 2 and not attempts[1]["sufficient"])
    chk("B3 k=1 also exposes a congruence obstruction",
        attempts[1]["right_congruent"] is False)
    chk("B4 GENESIS first stabilizes at four blocks",
        len(g) == 4 and lawful_and_sufficient(g) and attempts[-1]["k"] == 2,
        canonical(g))

    # C. SOLVENT: approach from too much structure.
    print("\n--- C. SOLVENT from above ---")
    singleton: Partition = tuple(frozenset({a}) for a in ATOMS)
    chk("C1 overcomplete singleton present is lawful+sufficient",
        len(singleton) == 8 and lawful_and_sufficient(singleton))
    chk("C2 no one-at-a-time lawful merge exists from the 8-state present",
        greedy_one_merge_exists(singleton) is False,
        "individual pruning gets stuck")

    s, report = solvent()
    print("   solvent_report:", report)
    chk("C3 SOLVENT exhausts the full Bell(8) partition lattice",
        report["partitions_examined"] == 4140,
        report["partitions_examined"])
    chk("C4 SOLVENT finds a four-block minimum",
        len(s) == 4 and report["minimum_block_count"] == 4)
    chk("C5 intermediate 7/6/5-block solutions do not exist",
        all(k not in report["valid_by_block_count"] for k in (5, 6, 7)),
        report["valid_by_block_count"])
    chk("C6 four-block solution is globally unique",
        report["n_minima"] == 1,
        f"n_minima={report['n_minima']}")

    # D. Independent convergence.
    print("\n--- D. Bidirectional convergence ---")
    chk("D1 GENESIS and SOLVENT converge on the same quotient",
        canonical(g) == canonical(s),
        f"G={canonical(g)} S={canonical(s)}")
    chk("D2 survivor is jointly minimal among lawful+sufficient presents",
        report["minimum_block_count"] == distinct_warrant_classes == 4)
    chk("D3 contraction is strict from above",
        len(singleton) > len(s))

    # E. Negative controls.
    print("\n--- E. Negative controls ---")
    underfit = force_underfit_from_minimum(s)
    chk("E1 forced three-block quotient fails frozen consequence",
        len(underfit) == 3 and warrant_sufficient(underfit) is False)
    chk("E2 forced underfit is rejected by lawful+sufficient gate",
        lawful_and_sufficient(underfit) is False)
    chk("E3 overfit eight-block present is sufficient but not minimal",
        lawful_and_sufficient(singleton) and len(singleton) > report["minimum_block_count"])

    # F. Fix the v2d frontier mistake explicitly.
    print("\n--- F. Warrant-constrained frontier ---")
    horizon_candidates = []
    for k in range(5):
        p = partition_from_horizon(k)
        if lawful_and_sufficient(p):
            horizon_candidates.append((len(p), k, canonical(p)))
    min_states = min(x[0] for x in horizon_candidates)
    frontier = [(k, n) for n, k, _ in horizon_candidates if n == min_states]
    chk("F1 inadequate k=0 is excluded from the admissible frontier",
        all(k != 0 for k, _ in frontier),
        frontier)
    chk("F2 frontier minimum is four states",
        min_states == 4,
        frontier)

    n_pass = sum(1 for _, ok, _ in checks if ok)
    n_total = len(checks)
    verdict = "PASS" if n_pass == n_total else "FAIL"

    print("\n--- Final convergence ---")
    print("  GENESIS :", canonical(g))
    print("  SOLVENT :", canonical(s))
    print("  valid_by_block_count:", report["valid_by_block_count"])
    print("  admissible_frontier:", frontier)

    print("\n" + "=" * 78)
    print(f"VERDICT: {verdict}   {n_pass}/{n_total} checks")
    if verdict == "PASS":
        print("VERIFIED_BIDIRECTIONAL_GENESIS_SOLVENT_CONVERGENCE_ON_JOINT_MINIMUM")
    print("=" * 78)

    if verdict != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""
MDA Recursive Residue Equation Test v1

Goal:
  Test the proposed recursive kernel exactly, including the difficult case
  where the warranted minimum is not unique.

Finite universe:
  Four atoms {0,1,2,3}; all 15 set partitions are exhaustively enumerated.
  Commitment order is refinement:
      Q <= P  means Q is no more committed than P (Q is a coarsening of P).
  A warrant is a frozen set of pairwise distinctions that consequence requires.
  A partition is sufficient iff every required pair is separated.

This isolates the developmental control law from domain-specific machinery.

The test does two things:
  1) Falsifies the scalar rule "one minimal sufficient P -> identity" when
     warrant admits multiple incomparable minima.
  2) Tests the corrected residue equation whose state is the entire warranted
     minimal antichain.

Corrected semantic recurrence:

    R_{t+1} =
      R_t,                                      if warrant is inadequate
      Min_<= { P : A_Omega(P) },                otherwise

GENESIS and SOLVENT become directional implementations/diagnostics relative
to this target residue; they are not the semantic definition of the target.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import FrozenSet, Iterable, Iterator, List, Sequence, Set, Tuple

Atom = int
Block = FrozenSet[Atom]
Partition = Tuple[Block, ...]
Frontier = FrozenSet[Partition]

ATOMS: Tuple[Atom, ...] = (0, 1, 2, 3)


def canon_partition(part: Iterable[Iterable[Atom]]) -> Partition:
    blocks = [frozenset(b) for b in part]
    return tuple(sorted(blocks, key=lambda b: tuple(sorted(b))))


def key(part: Partition):
    return tuple(tuple(sorted(b)) for b in part)


def set_partitions(items: Sequence[Atom]) -> Iterator[Partition]:
    blocks: List[List[Atom]] = []

    def rec(i: int):
        if i == len(items):
            yield canon_partition(blocks)
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


ALL_PARTITIONS: Tuple[Partition, ...] = tuple(sorted(set(set_partitions(ATOMS)), key=lambda p: (len(p), key(p))))
assert len(ALL_PARTITIONS) == 15


def block_of(part: Partition, atom: Atom) -> int:
    for i, b in enumerate(part):
        if atom in b:
            return i
    raise KeyError(atom)


def separates(part: Partition, a: Atom, b: Atom) -> bool:
    return block_of(part, a) != block_of(part, b)


def coarser_or_equal(q: Partition, p: Partition) -> bool:
    """q <= p in commitment order: every p-block sits inside some q-block."""
    for pb in p:
        if not any(pb <= qb for qb in q):
            return False
    return True


def strictly_coarser(q: Partition, p: Partition) -> bool:
    return q != p and coarser_or_equal(q, p)


def strictly_finer(q: Partition, p: Partition) -> bool:
    return q != p and coarser_or_equal(p, q)


@dataclass(frozen=True)
class Warrant:
    name: str
    adequate: bool
    required_separations: FrozenSet[Tuple[Atom, Atom]]


def W(name: str, adequate: bool, edges: Iterable[Tuple[int, int]]) -> Warrant:
    return Warrant(
        name=name,
        adequate=adequate,
        required_separations=frozenset(tuple(sorted(e)) for e in edges),
    )


# Unique 2-block minimum: connected bipartite K2,2.
OMEGA_A = W("A_unique_two", True, [(0,2),(0,3),(1,2),(1,3)])

# Unique 4-block minimum: complete graph K4.
OMEGA_B = W("B_unique_four", True, combinations(ATOMS, 2))

# Two incomparable 2-block minima: two disconnected required distinctions.
OMEGA_C = W("C_ambiguous_two", True, [(0,1),(2,3)])

# Unique 1-block minimum: no distinction currently required.
OMEGA_D = W("D_release_all", True, [])

# Inadequate authority: no scientifically licensed update.
OMEGA_U = W("U_inadequate", False, [(0,1)])


def admissible(part: Partition, omega: Warrant) -> bool:
    if not omega.adequate:
        return False
    return all(separates(part, a, b) for a, b in omega.required_separations)


def global_minimal_frontier(omega: Warrant) -> Frontier:
    if not omega.adequate:
        raise ValueError("frontier undefined under inadequate warrant")

    good = [p for p in ALL_PARTITIONS if admissible(p, omega)]
    mins = []
    for p in good:
        if not any(strictly_coarser(q, p) and admissible(q, omega) for q in good):
            mins.append(p)
    return frozenset(mins)


def scalar_classify(p: Partition, omega: Warrant) -> str:
    if not omega.adequate:
        return "UNKNOWN"
    if not admissible(p, omega):
        return "INSUFFICIENT"
    if any(strictly_coarser(q, p) and admissible(q, omega) for q in ALL_PARTITIONS):
        return "REDUCIBLE"
    return "MINIMAL_SUFFICIENT"


def scalar_genesis(p: Partition, omega: Warrant) -> Frontier:
    """Least-commitment admissible refinements reachable without merging old blocks."""
    candidates = [q for q in ALL_PARTITIONS if (q == p or strictly_finer(q, p)) and admissible(q, omega)]
    if not candidates:
        return frozenset()
    min_blocks = min(len(q) for q in candidates)
    return frozenset(q for q in candidates if len(q) == min_blocks)


def scalar_solvent(p: Partition, omega: Warrant) -> Frontier:
    """Greatest warranted dissolution among coarsenings of p."""
    candidates = [q for q in ALL_PARTITIONS if coarser_or_equal(q, p) and admissible(q, omega)]
    if not candidates:
        return frozenset()
    min_blocks = min(len(q) for q in candidates)
    return frozenset(q for q in candidates if len(q) == min_blocks)


def scalar_step(frontier: Frontier, omega: Warrant):
    """
    Literal lift of the proposed scalar rule over each currently-held present.
    This deliberately does NOT globally invent lateral alternatives.
    """
    if not omega.adequate:
        return frontier, frozenset({"UNKNOWN"})

    out: Set[Partition] = set()
    actions: Set[str] = set()

    for p in frontier:
        cls = scalar_classify(p, omega)
        if cls == "INSUFFICIENT":
            actions.add("GENESIS")
            out.update(scalar_genesis(p, omega))
        elif cls == "REDUCIBLE":
            actions.add("SOLVENT")
            out.update(scalar_solvent(p, omega))
        elif cls == "MINIMAL_SUFFICIENT":
            actions.add("IDENTITY")
            out.add(p)
        else:
            raise AssertionError(cls)

    return frozenset(out), frozenset(actions)


def scalar_close(frontier: Frontier, omega: Warrant, max_steps=10):
    trace = []
    seen = set()
    cur = frontier
    for i in range(max_steps):
        token = tuple(sorted(key(p) for p in cur))
        if token in seen:
            return cur, trace, "CYCLE"
        seen.add(token)

        nxt, actions = scalar_step(cur, omega)
        trace.append((i, cur, actions, nxt))

        if "UNKNOWN" in actions:
            return cur, trace, "UNKNOWN"
        if nxt == cur and actions == frozenset({"IDENTITY"}):
            return cur, trace, "FIXED"
        cur = nxt

    return cur, trace, "LIMIT"


def residue_update(current: Frontier, omega: Warrant):
    """
    Correct semantic recurrence. If authority is inadequate, preserve current
    alternatives. Otherwise return the entire minimal admissible antichain.
    """
    if not omega.adequate:
        return current, "UNKNOWN"
    target = global_minimal_frontier(omega)
    return target, movement_label(current, target)


def frontier_refines(new: Frontier, old: Frontier) -> bool:
    """Every new present is at least as committed as some old present."""
    return all(any(coarser_or_equal(o, n) for o in old) for n in new)


def frontier_coarsens(new: Frontier, old: Frontier) -> bool:
    """Every new present is no more committed than some old present."""
    return all(any(coarser_or_equal(n, o) for o in old) for n in new)


def movement_label(old: Frontier, new: Frontier) -> str:
    if new == old:
        return "IDENTITY"
    grows = frontier_refines(new, old)
    dissolves = frontier_coarsens(new, old)
    if grows and not dissolves:
        return "GENESIS"
    if dissolves and not grows:
        return "SOLVENT"
    return "RELOCATE"


def fmt_frontier(fr: Frontier) -> str:
    return "{" + ", ".join(str(key(p)) for p in sorted(fr, key=key)) + "}"


def run():
    checks = []

    def chk(name: str, cond: bool, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 88)
    print("MDA RECURSIVE RESIDUE EQUATION TEST v1")
    print("=" * 88)
    print(f"partition_lattice_size={len(ALL_PARTITIONS)} (Bell(4))")

    least = frozenset({canon_partition([ATOMS])})

    # ------------------------------------------------------------------
    # A. Ground truth frontiers, exhaustively computed.
    # ------------------------------------------------------------------
    print("\n--- A. Exhaustive warranted minima ---")
    FA = global_minimal_frontier(OMEGA_A)
    FB = global_minimal_frontier(OMEGA_B)
    FC = global_minimal_frontier(OMEGA_C)
    FD = global_minimal_frontier(OMEGA_D)

    print(" A:", fmt_frontier(FA))
    print(" B:", fmt_frontier(FB))
    print(" C:", fmt_frontier(FC))
    print(" D:", fmt_frontier(FD))

    chk("A1 A has one unique 2-block minimum", len(FA) == 1 and all(len(p) == 2 for p in FA))
    chk("A2 B has one unique 4-block minimum", len(FB) == 1 and all(len(p) == 4 for p in FB))
    chk("A3 C has exactly two incomparable 2-block minima",
        len(FC) == 2 and all(len(p) == 2 for p in FC)
        and not any(coarser_or_equal(x, y) for x in FC for y in FC if x != y),
        fmt_frontier(FC))
    chk("A4 D releases all distinctions to one block", FD == least)

    # ------------------------------------------------------------------
    # B. Falsify the scalar fixed-point rule on lateral alternatives.
    # ------------------------------------------------------------------
    print("\n--- B. Scalar equation negative control ---")
    one_C = frozenset({sorted(FC, key=key)[0]})
    scalar_final, scalar_trace, scalar_status = scalar_close(one_C, OMEGA_C)

    for i, before, actions, after in scalar_trace:
        print(f" scalar step {i}: actions={sorted(actions)} before={fmt_frontier(before)} after={fmt_frontier(after)}")

    chk("B1 chosen C-present is individually minimal sufficient",
        scalar_classify(next(iter(one_C)), OMEGA_C) == "MINIMAL_SUFFICIENT")
    chk("B2 literal scalar rule returns IDENTITY",
        scalar_status == "FIXED" and scalar_final == one_C)
    chk("B3 scalar identity is epistemically incomplete: it misses an equally warranted minimum",
        scalar_final != FC and scalar_final < FC,
        f"held={fmt_frontier(scalar_final)} true_frontier={fmt_frontier(FC)}")

    # ------------------------------------------------------------------
    # C. Correct recurrence preserves UNKNOWN and computes full residue.
    # ------------------------------------------------------------------
    print("\n--- C. Correct residue recurrence ---")
    cur = least
    cur2, action = residue_update(cur, OMEGA_U)
    chk("C1 inadequate warrant returns UNKNOWN", action == "UNKNOWN")
    chk("C2 UNKNOWN preserves the present exactly", cur2 == cur)

    cur, action = residue_update(cur, OMEGA_A)
    chk("C3 A forces GENESIS from one block to unique two-block residue",
        action == "GENESIS" and cur == FA,
        f"action={action} residue={fmt_frontier(cur)}")

    cur, action = residue_update(cur, OMEGA_B)
    chk("C4 richer consequence forces GENESIS two -> four",
        action == "GENESIS" and cur == FB,
        f"action={action}")

    cur, action = residue_update(cur, OMEGA_A)
    chk("C5 relaxed consequence forces SOLVENT four -> two",
        action == "SOLVENT" and cur == FA,
        f"action={action}")

    cur, action = residue_update(cur, OMEGA_C)
    chk("C6 changed warrant causes non-monotone RELOCATE to complete ambiguous frontier",
        action == "RELOCATE" and cur == FC,
        f"action={action} residue={fmt_frontier(cur)}")

    cur, action = residue_update(cur, OMEGA_D)
    chk("C7 release-all warrant dissolves both alternatives to one residue",
        action == "SOLVENT" and cur == FD,
        f"action={action}")

    cur, action = residue_update(cur, OMEGA_B)
    chk("C8 renewed strict warrant regrows one -> four",
        action == "GENESIS" and cur == FB,
        f"action={action}")

    # ------------------------------------------------------------------
    # D. Show RELOCATE is itself Genesis then Solvent under the same warrant.
    # ------------------------------------------------------------------
    print("\n--- D. Recursive decomposition of lateral boundary motion ---")
    from_A = FA
    step1, a1 = scalar_step(from_A, OMEGA_C)
    step2, a2 = scalar_step(step1, OMEGA_C)

    print(" from A under C:")
    print("   step1", sorted(a1), fmt_frontier(step1))
    print("   step2", sorted(a2), fmt_frontier(step2))

    chk("D1 first response to lateral move is GENESIS (split false equivalences)",
        a1 == frozenset({"GENESIS"}))
    chk("D2 second response is SOLVENT (erase now-unwarranted distinctions)",
        a2 == frozenset({"SOLVENT"}))
    chk("D3 Genesis then Solvent lands on the full C frontier",
        step2 == FC)
    chk("D4 RELOCATE is therefore not a fifth primitive",
        movement_label(FA, FC) == "RELOCATE" and step2 == global_minimal_frontier(OMEGA_C),
        "compound path = GENESIS -> SOLVENT")

    # ------------------------------------------------------------------
    # E. Universal finite check of the semantic equation.
    # ------------------------------------------------------------------
    print("\n--- E. Exhaustive state-space checks ---")
    adequate = [OMEGA_A, OMEGA_B, OMEGA_C, OMEGA_D]

    every_target_is_antichain = True
    every_target_is_admissible = True
    every_target_is_globally_minimal = True

    for omega in adequate:
        target = global_minimal_frontier(omega)
        for p in target:
            every_target_is_admissible &= admissible(p, omega)
            every_target_is_globally_minimal &= not any(
                strictly_coarser(q, p) and admissible(q, omega)
                for q in ALL_PARTITIONS
            )
        for x in target:
            for y in target:
                if x != y and (coarser_or_equal(x, y) or coarser_or_equal(y, x)):
                    every_target_is_antichain = False

    chk("E1 every adequate warrant returns an admissible frontier", every_target_is_admissible)
    chk("E2 every survivor is globally minimal under commitment order", every_target_is_globally_minimal)
    chk("E3 every returned residue is an antichain", every_target_is_antichain)

    # Every one of the 15 singleton starting presents must be overwritten by
    # the semantic recurrence to the exact same warranted residue for a fixed
    # adequate omega; history cannot change the answer.
    history_independent = True
    for omega in adequate:
        target = global_minimal_frontier(omega)
        for p in ALL_PARTITIONS:
            got, _ = residue_update(frozenset({p}), omega)
            if got != target:
                history_independent = False
                break
    chk("E4 exact residue is path-independent over all 15 starting presents x 4 warrants",
        history_independent,
        "60 exhaustive start/warrant cases")

    # UNKNOWN must preserve every starting present.
    unknown_preserves_all = True
    for p in ALL_PARTITIONS:
        got, act = residue_update(frozenset({p}), OMEGA_U)
        if got != frozenset({p}) or act != "UNKNOWN":
            unknown_preserves_all = False
            break
    chk("E5 inadequate warrant preserves all 15 possible starting presents",
        unknown_preserves_all)

    # ------------------------------------------------------------------
    # F. The equation itself.
    # ------------------------------------------------------------------
    print("\n--- F. Equation verdict ---")
    print("Candidate scalar equation fails B3 because a single minimal present")
    print("can omit equally warranted incomparable alternatives.")
    print()
    print("Correct state variable: R_t = warranted residue/frontier (an antichain).")
    print("Correct semantic recurrence:")
    print("  R_{t+1} = R_t                                      if warrant inadequate")
    print("  R_{t+1} = Min_<= {P : A_Omega_t(P)}                otherwise")
    print()
    print("GENESIS/SOLVENT are directional realization operators relative to that")
    print("frontier; RELOCATE decomposes recursively as GENESIS -> SOLVENT.")

    n_pass = sum(1 for _, ok, _ in checks if ok)
    n_total = len(checks)
    verdict = "PASS" if n_pass == n_total else "FAIL"

    print("\n" + "=" * 88)
    print(f"VERDICT: {verdict}   {n_pass}/{n_total} checks")
    if verdict == "PASS":
        print("VERIFIED_RECURSIVE_RESIDUE_EQUATION_WITH_ANTICHAIN_PRESENT")
        print("FALSIFIED_SCALAR_MINIMUM_IMPLIES_IDENTITY_WHEN_MINIMUM_IS_NONUNIQUE")
    print("=" * 88)

    if verdict != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    run()

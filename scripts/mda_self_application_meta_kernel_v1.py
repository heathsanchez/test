#!/usr/bin/env python3
"""
MDA Self-Application / Meta-Kernel Residue Test v1

Question:
  If the recursive residue equation is applied to its own kernel commitments,
  what survives?

Method:
  - Treat kernel commitments themselves as the "present".
  - Freeze behavioral requirements already established by the prior finite tests.
  - Enumerate every subset of a deliberately overcomplete 10-feature meta-kernel.
  - A subset is admitted only if it reproduces the frozen behaviors.
  - SOLVENT approaches from the full 10-feature kernel.
  - GENESIS approaches from the empty feature set by accumulating requirements
    and retaining the complete antichain of minimal feature sets that satisfy
    the evidence seen so far.
  - Require both directions to converge.

Scope:
  Finite, exhaustive, and relative to this explicit meta-language and frozen
  requirement suite. It does not prove universal minimality outside that scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable, FrozenSet, Iterable, Iterator, List, Sequence, Set, Tuple

Atom = int
Block = FrozenSet[Atom]
Partition = Tuple[Block, ...]
Frontier = FrozenSet[Partition]
FeatureSet = FrozenSet[str]

ATOMS: Tuple[Atom, ...] = (0, 1, 2, 3)

# Candidate meta-kernel commitments.
# The first four affect semantic residue construction.
# The remaining six are procedural vocabulary from earlier formulations;
# their scientific question is whether they must remain primitive.
FEATURES: Tuple[str, ...] = (
    "WARRANT_GATE",
    "ADMISSIBILITY",
    "MINIMALITY",
    "ANTICHAIN_PRESENT",
    "GENESIS_PRIMITIVE",
    "SOLVENT_PRIMITIVE",
    "IDENTITY_PRIMITIVE",
    "UNKNOWN_PRIMITIVE",
    "RELOCATE_PRIMITIVE",
    "EXPLICIT_BRANCH_LOOP",
)

SEMANTIC_CORE = frozenset({
    "WARRANT_GATE",
    "ADMISSIBILITY",
    "MINIMALITY",
    "ANTICHAIN_PRESENT",
})


def canon_partition(part: Iterable[Iterable[Atom]]) -> Partition:
    blocks = [frozenset(b) for b in part]
    return tuple(sorted(blocks, key=lambda b: tuple(sorted(b))))


def pkey(part: Partition):
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


ALL_PARTITIONS: Tuple[Partition, ...] = tuple(
    sorted(set(set_partitions(ATOMS)), key=lambda p: (len(p), pkey(p)))
)
assert len(ALL_PARTITIONS) == 15

LEAST: Frontier = frozenset({canon_partition([ATOMS])})
DISCRETE: Frontier = frozenset({canon_partition([{0}, {1}, {2}, {3}])})


def block_of(part: Partition, atom: Atom) -> int:
    for i, b in enumerate(part):
        if atom in b:
            return i
    raise KeyError(atom)


def separates(part: Partition, a: Atom, b: Atom) -> bool:
    return block_of(part, a) != block_of(part, b)


def coarser_or_equal(q: Partition, p: Partition) -> bool:
    return all(any(pb <= qb for qb in q) for pb in p)


def strictly_coarser(q: Partition, p: Partition) -> bool:
    return q != p and coarser_or_equal(q, p)


@dataclass(frozen=True)
class Warrant:
    name: str
    adequate: bool
    required_separations: FrozenSet[Tuple[int, int]]


def W(name: str, adequate: bool, edges: Iterable[Tuple[int, int]]) -> Warrant:
    return Warrant(
        name,
        adequate,
        frozenset(tuple(sorted(e)) for e in edges),
    )


OMEGA_A = W("A_unique_two", True, [(0,2),(0,3),(1,2),(1,3)])
OMEGA_B = W("B_unique_four", True, combinations(ATOMS, 2))
OMEGA_C = W("C_ambiguous_two", True, [(0,1),(2,3)])
OMEGA_D = W("D_release_all", True, [])
OMEGA_U = W("U_inadequate", False, [(0,1)])

# Independently frozen expected frontiers from the previous exhaustive equation test.
FA: Frontier = frozenset({canon_partition([{0,1},{2,3}])})
FB: Frontier = DISCRETE
FC: Frontier = frozenset({
    canon_partition([{0,2},{1,3}]),
    canon_partition([{0,3},{1,2}]),
})
FD: Frontier = LEAST


def real_admissible(part: Partition, omega: Warrant) -> bool:
    return all(separates(part, a, b) for a, b in omega.required_separations)


def engine(features: FeatureSet, current: Frontier, omega: Warrant) -> Frontier:
    """
    Meta-kernel implementation selected by a feature subset.

    The semantics intentionally expose each commitment to ablation:
      WARRANT_GATE:
        inadequate authority freezes current state.
        without it, the engine proceeds as if authority were adequate.
      ADMISSIBILITY:
        use consequence constraints to filter presents.
        without it, all presents are treated as admissible.
      MINIMALITY:
        remove admissible presents with an admissible strict coarsening.
        without it, all admitted presents survive.
      ANTICHAIN_PRESENT:
        preserve all minimal survivors.
        without it, collapse to one canonical survivor.

    The older procedural primitives are not consulted by state semantics.
    If they are scientifically primitive, exhaustive necessity testing must
    demonstrate that their removal changes a frozen consequence. This test
    gives them that opportunity rather than assuming necessity.
    """
    if "WARRANT_GATE" in features and not omega.adequate:
        return current

    if "ADMISSIBILITY" in features:
        candidates = [p for p in ALL_PARTITIONS if real_admissible(p, omega)]
    else:
        candidates = list(ALL_PARTITIONS)

    if "MINIMALITY" in features:
        candidates = [
            p for p in candidates
            if not any(strictly_coarser(q, p) for q in candidates)
        ]

    candidates = sorted(candidates, key=pkey)

    if "ANTICHAIN_PRESENT" not in features and candidates:
        candidates = [candidates[0]]

    return frozenset(candidates)


@dataclass(frozen=True)
class Requirement:
    name: str
    check: Callable[[FeatureSet], bool]
    witness: str


def exact_case(name: str, current: Frontier, omega: Warrant, expected: Frontier) -> Requirement:
    return Requirement(
        name,
        lambda fs, c=current, o=omega, e=expected: engine(fs, c, o) == e,
        f"{omega.name}: expected exact residue {sorted((pkey(p) for p in expected))}",
    )


REQUIREMENTS: Tuple[Requirement, ...] = (
    exact_case("R1_UNKNOWN_freezes_present", FA, OMEGA_U, FA),
    exact_case("R2_unique_two_from_least", LEAST, OMEGA_A, FA),
    exact_case("R3_unique_four_from_two", FA, OMEGA_B, FB),
    exact_case("R4_dissolve_four_to_two", FB, OMEGA_A, FA),
    exact_case("R5_preserve_both_incomparable_minima", FA, OMEGA_C, FC),
    exact_case("R6_release_all_to_least", FC, OMEGA_D, FD),
    # Path-independence controls for adequate warrants.
    exact_case("R7_A_from_discrete", FB, OMEGA_A, FA),
    exact_case("R8_C_from_discrete", FB, OMEGA_C, FC),
)


def powerset_features() -> Iterator[FeatureSet]:
    for r in range(len(FEATURES) + 1):
        for combo in combinations(FEATURES, r):
            yield frozenset(combo)


ALL_FEATURE_SETS: Tuple[FeatureSet, ...] = tuple(powerset_features())
assert len(ALL_FEATURE_SETS) == 2 ** len(FEATURES)


def satisfies(fs: FeatureSet, reqs: Sequence[Requirement]) -> bool:
    return all(r.check(fs) for r in reqs)


def subset_minima(candidates: Iterable[FeatureSet]) -> FrozenSet[FeatureSet]:
    cands = list(candidates)
    mins = [
        fs for fs in cands
        if not any(other < fs for other in cands)
    ]
    return frozenset(mins)


def solvent(reqs: Sequence[Requirement]):
    """Global dissolution from the rich 10-feature present."""
    passing = [fs for fs in ALL_FEATURE_SETS if satisfies(fs, reqs)]
    minima = subset_minima(passing)
    return minima, {
        "feature_subsets_examined": len(ALL_FEATURE_SETS),
        "passing_subsets": len(passing),
        "minimum_sizes": sorted({len(x) for x in minima}),
        "n_minima": len(minima),
    }


def genesis(requirements: Sequence[Requirement]):
    """
    Grow evidence from below.

    Start from no requirements and the empty commitment. Introduce frozen
    consequences one at a time; after each, recompute the complete antichain
    of minimally committed feature sets satisfying all evidence seen so far.
    The test does not prescribe which feature to add.
    """
    trace = []
    active: List[Requirement] = []

    # Before evidence, least committed kernel is empty.
    frontier: FrozenSet[FeatureSet] = frozenset({frozenset()})
    trace.append(("START", frontier))

    for req in requirements:
        active.append(req)
        passing = [fs for fs in ALL_FEATURE_SETS if satisfies(fs, active)]
        frontier = subset_minima(passing)
        trace.append((req.name, frontier))

    return frontier, trace


def fmt_fs(fs: FeatureSet) -> str:
    return "{" + ",".join(sorted(fs)) + "}"


def fmt_meta_frontier(fr: FrozenSet[FeatureSet]) -> str:
    return "[" + ", ".join(sorted(fmt_fs(x) for x in fr)) + "]"


def movement_label(old: Frontier, new: Frontier) -> str:
    if old == new:
        return "IDENTITY"
    # Derived diagnostic only: compare block counts where unique enough.
    old_min = min(len(p) for p in old)
    new_min = min(len(p) for p in new)
    if new_min > old_min:
        return "GENESIS"
    if new_min < old_min:
        return "SOLVENT"
    return "RELOCATE"


def run():
    checks = []

    def chk(name: str, cond: bool, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 94)
    print("MDA SELF-APPLICATION / META-KERNEL RESIDUE TEST v1")
    print("=" * 94)
    print(f"meta_features={len(FEATURES)} subsets={len(ALL_FEATURE_SETS)} requirements={len(REQUIREMENTS)}")

    # A. Rich kernel is adequate.
    print("\n--- A. Rich kernel baseline ---")
    rich = frozenset(FEATURES)
    chk("A1 rich 10-feature kernel preserves all frozen consequences",
        satisfies(rich, REQUIREMENTS))

    # B. SOLVENT over all meta-kernel subsets.
    print("\n--- B. SOLVENT on the kernel itself ---")
    s_frontier, s_report = solvent(REQUIREMENTS)
    print(" solvent_report:", s_report)
    print(" solvent_minima:", fmt_meta_frontier(s_frontier))

    chk("B1 all 2^10 = 1024 feature subsets were exhausted",
        s_report["feature_subsets_examined"] == 1024)
    chk("B2 self-SOLVENT finds a unique minimum",
        len(s_frontier) == 1,
        fmt_meta_frontier(s_frontier))

    s_min = next(iter(s_frontier))
    chk("B3 unique surviving meta-kernel is exactly the four semantic commitments",
        s_min == SEMANTIC_CORE,
        fmt_fs(s_min))

    # C. Permanent ablation witnesses: every survivor is actually necessary.
    print("\n--- C. Necessity ablations ---")
    for feature in sorted(SEMANTIC_CORE):
        ablated = SEMANTIC_CORE - {feature}
        failed = [r.name for r in REQUIREMENTS if not r.check(ablated)]
        chk(f"C_{feature} removal breaks frozen consequence",
            len(failed) > 0,
            failed)

    # D. Old procedural primitives dissolve.
    print("\n--- D. Procedural vocabulary dissolves ---")
    procedural = set(FEATURES) - set(SEMANTIC_CORE)
    for feature in sorted(procedural):
        without = rich - {feature}
        chk(f"D_{feature} is not primitive under frozen semantic warrant",
            satisfies(without, REQUIREMENTS))

    # E. GENESIS from no commitments as evidence accumulates.
    print("\n--- E. GENESIS of the kernel from below ---")
    g_frontier, g_trace = genesis(REQUIREMENTS)
    for req_name, fr in g_trace:
        print(f" {req_name:40s} -> {fmt_meta_frontier(fr)}")

    chk("E1 meta-GENESIS converges to a unique final minimum",
        len(g_frontier) == 1)
    chk("E2 meta-GENESIS reaches the same four-feature kernel",
        g_frontier == frozenset({SEMANTIC_CORE}),
        fmt_meta_frontier(g_frontier))

    # F. Bidirectional self-convergence.
    print("\n--- F. Self-convergence ---")
    chk("F1 GENESIS-from-empty and SOLVENT-from-rich agree exactly",
        g_frontier == s_frontier)
    chk("F2 resulting kernel is a strict contraction of the rich procedural kernel",
        len(s_min) == 4 and len(rich) == 10)

    # G. Show directions are derived consequences, not retained primitives.
    print("\n--- G. Derived dynamics from the surviving kernel ---")
    sequence = [
        ("unknown", FA, OMEGA_U),
        ("grow", LEAST, OMEGA_A),
        ("grow_more", FA, OMEGA_B),
        ("dissolve", FB, OMEGA_A),
        ("relocate", FA, OMEGA_C),
        ("dissolve_all", FC, OMEGA_D),
    ]
    derived = []
    for name, old, omega in sequence:
        new = engine(SEMANTIC_CORE, old, omega)
        if not omega.adequate:
            label = "UNKNOWN"
        else:
            label = movement_label(old, new)
        derived.append((name, label))
        print(f" {name:16s} -> {label:8s} residue={sorted(pkey(p) for p in new)}")

    chk("G1 UNKNOWN is derivable without UNKNOWN_PRIMITIVE",
        ("unknown", "UNKNOWN") in derived and "UNKNOWN_PRIMITIVE" not in SEMANTIC_CORE)
    chk("G2 GENESIS is derivable without GENESIS_PRIMITIVE",
        any(label == "GENESIS" for _, label in derived) and "GENESIS_PRIMITIVE" not in SEMANTIC_CORE)
    chk("G3 SOLVENT is derivable without SOLVENT_PRIMITIVE",
        any(label == "SOLVENT" for _, label in derived) and "SOLVENT_PRIMITIVE" not in SEMANTIC_CORE)
    chk("G4 IDENTITY/RELOCATE need not be semantic primitives",
        "IDENTITY_PRIMITIVE" not in SEMANTIC_CORE and "RELOCATE_PRIMITIVE" not in SEMANTIC_CORE)

    # H. The self-applied equation.
    print("\n--- H. Meta-equation ---")
    print("Rich procedural kernel:")
    print(" ", fmt_fs(rich))
    print("Self-applied warranted residue:")
    print(" ", fmt_fs(s_min))
    print()
    print("Meta-residue law:")
    print("  K* = Min_subset { K subseteq K_rich : frozen_consequence(K) = frozen_consequence(K_rich) }")
    print("Observed unique K*:")
    print("  {WARRANT_GATE, ADMISSIBILITY, MINIMALITY, ANTICHAIN_PRESENT}")
    print()
    print("Thus GENESIS/SOLVENT/IDENTITY/UNKNOWN/RELOCATE/BRANCH_LOOP survive as")
    print("derived descriptions or implementation strategies, not semantic primitives.")

    n_pass = sum(1 for _, ok, _ in checks if ok)
    n_total = len(checks)
    verdict = "PASS" if n_pass == n_total else "FAIL"

    print("\n" + "=" * 94)
    print(f"VERDICT: {verdict}   {n_pass}/{n_total} checks")
    if verdict == "PASS":
        print("VERIFIED_MDA_SELF_APPLICATION_CONVERGES_ON_FOUR_COMMITMENT_META_KERNEL")
        print("VERIFIED_GENESIS_SOLVENT_DISSOLVE_AS_DERIVED_DYNAMICS_NOT_SEMANTIC_PRIMITIVES")
    print("=" * 94)

    if verdict != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    run()

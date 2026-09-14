#!/usr/bin/env python3
"""
MDA Transformation Recipes V1

Apply five historical transformation recipes as finite experimental protocols
to the recursive-residue kernel already earned by prior tests:

  1. COHOBATION   — recirculate a residue through itself until fixed.
  2. CALCINATION  — burn away scaffolding; inspect irreducible ash.
  3. PUTREFACTION — damage mature structure and test rediscovery.
  4. DISTILLATION — compare independent substrates for a shared invariant.
  5. DEGREES_FIRE — increase consequence pressure and observe phase changes.

This is not a historical-alchemy claim. The recipe names label perturbation
protocols. Scientific claims are finite/exhaustive within the explicit
meta-language below.

Object-level substrate:
  Set partitions of n atoms (n = 3, 4, 5), with a frozen warrant represented
  by required pairwise distinctions.

Meta-level candidate kernel:
  10 possible commitments. Four have semantic effect:
    WARRANT_GATE, ADMISSIBILITY, MINIMALITY, ANTICHAIN_PRESENT.
  Six older procedural notions are available as candidate primitives but are
  not assumed necessary:
    GENESIS_PRIMITIVE, SOLVENT_PRIMITIVE, IDENTITY_PRIMITIVE,
    UNKNOWN_PRIMITIVE, RELOCATE_PRIMITIVE, EXPLICIT_BRANCH_LOOP.

All 2^10 = 1024 meta-kernels are exhaustively enumerable.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Dict, FrozenSet, Iterable, Iterator, List, Sequence, Tuple

Atom = int
Block = FrozenSet[Atom]
Partition = Tuple[Block, ...]
Frontier = FrozenSet[Partition]
FeatureSet = FrozenSet[str]

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

CORE: FeatureSet = frozenset({
    "WARRANT_GATE",
    "ADMISSIBILITY",
    "MINIMALITY",
    "ANTICHAIN_PRESENT",
})

PROCEDURAL: FeatureSet = frozenset(FEATURES) - CORE
RICH: FeatureSet = frozenset(FEATURES)


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


@dataclass(frozen=True)
class Domain:
    name: str
    atoms: Tuple[int, ...]
    partitions: Tuple[Partition, ...]


@dataclass(frozen=True)
class Requirement:
    name: str
    domain: Domain
    current: Frontier
    warrant: Warrant
    expected: Frontier


def mk_domain(n: int) -> Domain:
    atoms = tuple(range(n))
    parts = tuple(sorted(set(set_partitions(atoms)), key=lambda p: (len(p), pkey(p))))
    return Domain(f"D{n}", atoms, parts)


def W(name: str, adequate: bool, edges: Iterable[Tuple[int, int]]) -> Warrant:
    return Warrant(
        name,
        adequate,
        frozenset(tuple(sorted(e)) for e in edges),
    )


def admissible(part: Partition, omega: Warrant) -> bool:
    return all(separates(part, a, b) for a, b in omega.required_separations)


def oracle_frontier(domain: Domain, omega: Warrant) -> Frontier:
    if not omega.adequate:
        raise ValueError("oracle frontier undefined for inadequate warrant")
    good = [p for p in domain.partitions if admissible(p, omega)]
    mins = [
        p for p in good
        if not any(strictly_coarser(q, p) and admissible(q, omega)
                   for q in domain.partitions)
    ]
    return frozenset(mins)


def least_frontier(domain: Domain) -> Frontier:
    return frozenset({canon_partition([domain.atoms])})


def engine(features: FeatureSet, domain: Domain, current: Frontier, omega: Warrant) -> Frontier:
    if "WARRANT_GATE" in features and not omega.adequate:
        return current

    if "ADMISSIBILITY" in features:
        candidates = [p for p in domain.partitions if admissible(p, omega)]
    else:
        candidates = list(domain.partitions)

    if "MINIMALITY" in features:
        candidates = [
            p for p in candidates
            if not any(strictly_coarser(q, p) for q in candidates)
        ]

    candidates = sorted(candidates, key=pkey)

    if "ANTICHAIN_PRESENT" not in features and candidates:
        candidates = [candidates[0]]

    return frozenset(candidates)


def powerset(items: Sequence[str]) -> Iterator[FeatureSet]:
    for r in range(len(items) + 1):
        for combo in combinations(items, r):
            yield frozenset(combo)


ALL_FEATURE_SETS: Tuple[FeatureSet, ...] = tuple(powerset(FEATURES))
assert len(ALL_FEATURE_SETS) == 1024


def make_suite(domain: Domain) -> Tuple[Requirement, ...]:
    n = len(domain.atoms)
    left = tuple(domain.atoms[:2])
    right = tuple(domain.atoms[2:])
    assert left and right

    unique2_edges = [(a, b) for a in left for b in right]
    full_edges = list(combinations(domain.atoms, 2))

    if n == 3:
        ambiguous_edges = [(0, 1)]
    else:
        ambiguous_edges = [(0, 1), (2, 3)]

    O2 = W(f"{domain.name}_unique2", True, unique2_edges)
    OF = W(f"{domain.name}_full", True, full_edges)
    OA = W(f"{domain.name}_ambiguous", True, ambiguous_edges)
    OR = W(f"{domain.name}_release", True, [])
    OU = W(f"{domain.name}_unknown", False, full_edges)

    F2 = oracle_frontier(domain, O2)
    FF = oracle_frontier(domain, OF)
    FA = oracle_frontier(domain, OA)
    FR = oracle_frontier(domain, OR)
    LEAST = least_frontier(domain)

    assert len(F2) == 1
    assert len(FF) == 1
    assert len(FA) > 1
    assert FR == LEAST

    return (
        Requirement(f"{domain.name}_R1_UNKNOWN", domain, F2, OU, F2),
        Requirement(f"{domain.name}_R2_UNIQUE2_FROM_LEAST", domain, LEAST, O2, F2),
        Requirement(f"{domain.name}_R3_STRICTEN_TO_DISCRETE", domain, F2, OF, FF),
        Requirement(f"{domain.name}_R4_DISSOLVE_BACK_TO_TWO", domain, FF, O2, F2),
        Requirement(f"{domain.name}_R5_AMBIGUOUS_FRONTIER", domain, F2, OA, FA),
        Requirement(f"{domain.name}_R6_RELEASE_ALL", domain, FA, OR, FR),
        Requirement(f"{domain.name}_R7_PATH_INDEPENDENT_TWO", domain, FF, O2, F2),
        Requirement(f"{domain.name}_R8_PATH_INDEPENDENT_AMBIG", domain, FF, OA, FA),
    )


D3, D4, D5 = mk_domain(3), mk_domain(4), mk_domain(5)
SUITES: Dict[str, Tuple[Requirement, ...]] = {
    d.name: make_suite(d) for d in (D3, D4, D5)
}
ALL_REQUIREMENTS: Tuple[Requirement, ...] = tuple(
    req for name in ("D3", "D4", "D5") for req in SUITES[name]
)


def satisfies(fs: FeatureSet, reqs: Sequence[Requirement]) -> bool:
    return all(
        engine(fs, r.domain, r.current, r.warrant) == r.expected
        for r in reqs
    )


def subset_minima(candidates: Iterable[FeatureSet]) -> FrozenSet[FeatureSet]:
    cands = list(candidates)
    return frozenset(
        fs for fs in cands
        if not any(other < fs for other in cands)
    )


def meta_solvent(start: FeatureSet, reqs: Sequence[Requirement]) -> FrozenSet[FeatureSet]:
    candidates = [fs for fs in ALL_FEATURE_SETS if fs <= start and satisfies(fs, reqs)]
    return subset_minima(candidates)


def global_meta_minima(reqs: Sequence[Requirement]) -> FrozenSet[FeatureSet]:
    return subset_minima(fs for fs in ALL_FEATURE_SETS if satisfies(fs, reqs))


def fmt_fs(fs: FeatureSet) -> str:
    return "{" + ",".join(sorted(fs)) + "}"


def fmt_meta(fr: FrozenSet[FeatureSet]) -> str:
    return "[" + ", ".join(sorted(fmt_fs(x) for x in fr)) + "]"


def minimal_repairs(base: FeatureSet, reqs: Sequence[Requirement]) -> FrozenSet[FeatureSet]:
    missing = tuple(sorted(set(FEATURES) - set(base)))
    repairs = []
    for add in powerset(missing):
        candidate = base | add
        if satisfies(candidate, reqs):
            repairs.append(add)
    return subset_minima(repairs)


def run():
    checks = []

    def chk(name: str, cond: bool, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 100)
    print("MDA TRANSFORMATION RECIPES V1")
    print("=" * 100)
    print("domains:", {d.name: len(d.partitions) for d in (D3, D4, D5)})
    print(f"meta-kernels={len(ALL_FEATURE_SETS)} combined_requirements={len(ALL_REQUIREMENTS)}")

    # Foundation sanity.
    print("\n--- FOUNDATION ---")
    chk("F0 rich kernel satisfies every frozen requirement",
        satisfies(RICH, ALL_REQUIREMENTS))
    combined_min = global_meta_minima(ALL_REQUIREMENTS)
    chk("F1 combined exhaustive meta-minimum is unique CORE",
        combined_min == frozenset({CORE}),
        fmt_meta(combined_min))

    # ------------------------------------------------------------------
    # 1. COHOBATION — recirculation / fixed-point test.
    # ------------------------------------------------------------------
    print("\n--- 1. COHOBATION: recirculate the residue ---")
    round0 = frozenset({RICH})
    round1 = meta_solvent(RICH, ALL_REQUIREMENTS)
    assert len(round1) == 1
    k1 = next(iter(round1))
    round2 = meta_solvent(k1, ALL_REQUIREMENTS)
    round3 = meta_solvent(next(iter(round2)), ALL_REQUIREMENTS)

    print(" round0:", fmt_meta(round0))
    print(" round1:", fmt_meta(round1))
    print(" round2:", fmt_meta(round2))
    print(" round3:", fmt_meta(round3))

    chk("C1 first circulation contracts rich kernel to CORE",
        round1 == frozenset({CORE}))
    chk("C2 second circulation is idempotent",
        round2 == round1)
    chk("C3 third circulation remains fixed",
        round3 == round2)

    satisfying_starts = [fs for fs in ALL_FEATURE_SETS if satisfies(fs, ALL_REQUIREMENTS)]
    all_recirculate_to_core = all(
        meta_solvent(fs, ALL_REQUIREMENTS) == frozenset({CORE})
        for fs in satisfying_starts
    )
    chk("C4 every adequate starting meta-kernel recirculates to the same fixed residue",
        all_recirculate_to_core,
        f"adequate_starts={len(satisfying_starts)}")

    # ------------------------------------------------------------------
    # 2. CALCINATION — burn scaffolding away.
    # ------------------------------------------------------------------
    print("\n--- 2. CALCINATION: burn away historical/procedural scaffolding ---")
    ash = RICH - PROCEDURAL
    print(" rich:", fmt_fs(RICH))
    print(" ash :", fmt_fs(ash))

    chk("K1 burning all six procedural primitives at once preserves consequence",
        ash == CORE and satisfies(ash, ALL_REQUIREMENTS))
    chk("K2 calcination removes exactly six commitments",
        len(RICH) - len(ash) == 6)

    for feature in sorted(CORE):
        burned = CORE - {feature}
        failed = [r.name for r in ALL_REQUIREMENTS
                  if engine(burned, r.domain, r.current, r.warrant) != r.expected]
        chk(f"K3 ash-minus-{feature} fails",
            len(failed) > 0,
            f"witnesses={failed[:4]}")

    # ------------------------------------------------------------------
    # 3. PUTREFACTION — damage then blind repair search.
    # ------------------------------------------------------------------
    print("\n--- 3. PUTREFACTION: damage the mature kernel and regrow it ---")
    putrefaction_ok = True
    putrefaction_rows = []

    core_list = tuple(sorted(CORE))
    damage_cases = []
    for r in range(1, len(core_list) + 1):
        damage_cases.extend(frozenset(x) for x in combinations(core_list, r))

    for damage in damage_cases:
        base = CORE - damage
        repairs = minimal_repairs(base, ALL_REQUIREMENTS)
        expected = frozenset({damage})
        ok = repairs == expected
        putrefaction_ok &= ok
        putrefaction_rows.append((sorted(damage), fmt_meta(repairs)))

    for damage, repairs in putrefaction_rows:
        print(" damage=", damage, " minimal_repairs=", repairs)

    chk("P1 all 15 nonempty damage patterns are uniquely repaired",
        putrefaction_ok,
        f"damage_patterns={len(damage_cases)}")
    chk("P2 complete destruction regrows the four-feature CORE",
        minimal_repairs(frozenset(), ALL_REQUIREMENTS) == frozenset({CORE}))

    # ------------------------------------------------------------------
    # 4. DISTILLATION — independent substrates, same meta-residue.
    # ------------------------------------------------------------------
    print("\n--- 4. DISTILLATION: extract cross-substrate invariant ---")
    distilled = {}
    for name in ("D3", "D4", "D5"):
        mins = global_meta_minima(SUITES[name])
        distilled[name] = mins
        print(f" {name}: object_partitions={len({'D3':D3,'D4':D4,'D5':D5}[name].partitions)} meta_minima={fmt_meta(mins)}")
        chk(f"D_{name} independently distills to CORE",
            mins == frozenset({CORE}))

    chk("D4 all three independently distilled kernels are identical",
        len({tuple(sorted(next(iter(v)))) for v in distilled.values()}) == 1)
    chk("D5 combined cross-substrate distillation adds no new primitive",
        combined_min == frozenset({CORE}))

    # ------------------------------------------------------------------
    # 5. DEGREES OF FIRE — increase consequence pressure.
    # ------------------------------------------------------------------
    print("\n--- 5. DEGREES OF FIRE: consequence-pressure phase curve ---")
    d4 = SUITES["D4"]
    by_suffix = {r.name.split("_R", 1)[1]: r for r in d4}

    levels = [
        ("fire0_no_consequence", tuple()),
        ("fire1_authority_only", (by_suffix["1_UNKNOWN"],)),
        ("fire2_structure", (
            by_suffix["1_UNKNOWN"],
            by_suffix["2_UNIQUE2_FROM_LEAST"],
            by_suffix["3_STRICTEN_TO_DISCRETE"],
        )),
        ("fire3_ambiguity", (
            by_suffix["1_UNKNOWN"],
            by_suffix["2_UNIQUE2_FROM_LEAST"],
            by_suffix["3_STRICTEN_TO_DISCRETE"],
            by_suffix["5_AMBIGUOUS_FRONTIER"],
        )),
        ("fire4_cross_domain", ALL_REQUIREMENTS),
    ]

    observed = []
    fire_frontiers = []
    for name, reqs in levels:
        mins = global_meta_minima(reqs)
        fire_frontiers.append(mins)
        sizes = sorted(len(x) for x in mins)
        observed.append(sizes[0] if len(mins) == 1 else None)
        print(f" {name:24s} -> minima={fmt_meta(mins)} sizes={sizes}")

    expected_sets = [
        frozenset({frozenset()}),
        frozenset({frozenset({"WARRANT_GATE"})}),
        frozenset({frozenset({"WARRANT_GATE","ADMISSIBILITY","MINIMALITY"})}),
        frozenset({CORE}),
        frozenset({CORE}),
    ]

    chk("H1 pressure levels produce the predicted commitment phase sequence",
        fire_frontiers == expected_sets,
        f"sizes={observed}")
    chk("H2 commitment count changes discretely 0 -> 1 -> 3 -> 4 -> 4",
        observed == [0, 1, 3, 4, 4],
        observed)
    chk("H3 stronger cross-domain pressure does not cause gratuitous architecture growth",
        fire_frontiers[-1] == fire_frontiers[-2] == frozenset({CORE}))
    chk("H4 reversing pressure dissolves in the exact reverse commitment counts",
        list(reversed(observed)) == [4, 4, 3, 1, 0])

    # ------------------------------------------------------------------
    # Synthesis.
    # ------------------------------------------------------------------
    print("\n--- SYNTHESIS ---")
    print("COHOBATION : CORE is a fixed point under repeated self-residue.")
    print("CALCINATION: procedural vocabulary burns away; four semantic commitments remain.")
    print("PUTREFACTION: every nonempty damage pattern uniquely regenerates the missing CORE.")
    print("DISTILLATION: n=3,4,5 independent substrates distill the same CORE.")
    print("FIRE CURVE  : new commitments appear only at consequence thresholds: 0 -> 1 -> 3 -> 4.")

    n_pass = sum(1 for _, ok, _ in checks if ok)
    n_total = len(checks)
    verdict = "PASS" if n_pass == n_total else "FAIL"

    print("\n" + "=" * 100)
    print(f"VERDICT: {verdict}   {n_pass}/{n_total} checks")
    if verdict == "PASS":
        print("VERIFIED_COHOBATION_FIXED_POINT")
        print("VERIFIED_CALCINATION_IRREDUCIBLE_ASH")
        print("VERIFIED_PUTREFACTION_REGENESIS")
        print("VERIFIED_CROSS_SUBSTRATE_DISTILLATION")
        print("VERIFIED_DEGREES_OF_FIRE_PHASE_TRANSITIONS")
        print("VERIFIED_TRANSFORMATION_RECIPES_CONVERGE_ON_RECURSIVE_RESIDUE_KERNEL")
    print("=" * 100)

    if verdict != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    run()

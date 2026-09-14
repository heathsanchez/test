#!/usr/bin/env python3
"""
Warranted Consequential Difference V1 — dedicated falsification suite.

IMPORTANT:
- The candidate was frozen first at commit:
    978af4e94815128b4c517562f9a0bae26eea1e55
- This suite is authored after that freeze.
- It does not modify the candidate.
- The purpose is to attack the candidate and distinguish it from tempting
  simplifications.

Finite exhaustive components:
1. All binary consequence profiles for two candidate presents over two
   authorized futures (16 possible worlds), across all 65,535 nonempty
   compatible-world sets.
2. All 256 Boolean consequence functions over the 2^3 configurations of
   three structural components.

Additional explicit adversarial constructions:
3. right-congruence failure for a descriptive quotient used as executable state.
4. ground-vs-preference ordering.
5. self-application to developmental machinery as candidate presents.
"""

from __future__ import annotations

from itertools import product, combinations
from typing import Dict, FrozenSet, Iterable, List, Sequence, Tuple

FROZEN_COMMIT = "978af4e94815128b4c517562f9a0bae26eea1e55"

# ---------------------------------------------------------------------------
# Consequential relation
# ---------------------------------------------------------------------------

# A world is (P_profile, Q_profile), each profile is a tuple of binary
# consequences indexed by authorized future continuation.
Profile = Tuple[int, ...]
World = Tuple[Profile, Profile]


def dist(worlds: Sequence[World]) -> bool:
    """forall world exists authorized future with differing consequence."""
    return all(any(a != b for a, b in zip(p, q)) for p, q in worlds)


def rsep(worlds: Sequence[World]) -> bool:
    """exists one common future that separates in every compatible world."""
    n = len(worlds[0][0])
    return any(all(w[0][i] != w[1][i] for w in worlds) for i in range(n))


def eq(worlds: Sequence[World]) -> bool:
    """forall world forall authorized future consequences agree."""
    return all(all(a == b for a, b in zip(p, q)) for p, q in worlds)


def status(worlds: Sequence[World]) -> str:
    d, e = dist(worlds), eq(worlds)
    if d and e:
        raise AssertionError("DIST and EQ must be disjoint")
    if d:
        return "DIST"
    if e:
        return "EQ"
    return "UNKNOWN"


def correction(currently_merged: bool, relation_status: str) -> str:
    if currently_merged and relation_status == "DIST":
        return "SPLIT"
    if (not currently_merged) and relation_status == "EQ":
        return "MERGE"
    return "DO_NOT_YET_DECIDE"


# ---------------------------------------------------------------------------
# Joint-sufficiency realization frontier
# ---------------------------------------------------------------------------

FeatureSet = FrozenSet[str]


def powerset(items: Sequence[str]) -> List[FeatureSet]:
    out: List[FeatureSet] = []
    for r in range(len(items) + 1):
        for c in combinations(items, r):
            out.append(frozenset(c))
    return out


FEATURES = ("a", "b", "c")
CONFIGS = powerset(FEATURES)


def subset_minima(xs: Iterable[FeatureSet]) -> FrozenSet[FeatureSet]:
    arr = list(xs)
    return frozenset(x for x in arr if not any(y < x for y in arr))


def config_index(cfg: FeatureSet) -> int:
    # bit order a,b,c
    return sum((1 << i) for i, f in enumerate(FEATURES) if f in cfg)


def truth_value(mask: int, cfg: FeatureSet) -> int:
    return (mask >> config_index(cfg)) & 1


def frontier_for(mask: int, required_value: int = 1) -> FrozenSet[FeatureSet]:
    sufficient = [c for c in CONFIGS if truth_value(mask, c) == required_value]
    return subset_minima(sufficient)


def atomic_indispensable_from_full(mask: int) -> FrozenSet[str]:
    full = frozenset(FEATURES)
    base = truth_value(mask, full)
    return frozenset(
        f for f in FEATURES
        if truth_value(mask, full - {f}) != base
    )


# ---------------------------------------------------------------------------
# Dynamic quotient / right-congruence adversary
# ---------------------------------------------------------------------------


def right_congruence_counterexample():
    # Descriptive current-scope observation sees h1,h2 both as output 0.
    current_output = {"h1": 0, "h2": 0, "u": 0, "v": 1}
    # Both h1,h2 are grouped by current observation.
    equiv = lambda x, y: current_output[x] == current_output[y]
    # Authorized action 'a' sends the grouped histories to inequivalent successors.
    step = {("h1", "a"): "u", ("h2", "a"): "v"}
    descriptive_eq = equiv("h1", "h2")
    extension_preserves = equiv(step[("h1", "a")], step[("h2", "a")])
    return descriptive_eq, extension_preserves


# ---------------------------------------------------------------------------
# Ground / measurement / preference
# ---------------------------------------------------------------------------


def lawful_min(candidates: List[Dict]) -> List[str]:
    lawful = [c for c in candidates if c["ground_ok"]]
    best = min(c["cost"] for c in lawful)
    return sorted(c["name"] for c in lawful if c["cost"] == best)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run():
    checks = []

    def chk(name: str, cond: bool, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 100)
    print("WARRANTED CONSEQUENTIAL DIFFERENCE V1 — FALSIFICATION SUITE")
    print("frozen_candidate_commit =", FROZEN_COMMIT)
    print("=" * 100)

    # ------------------------------------------------------------------
    # A. Exhaustive epistemic trichotomy over all compatible-world sets.
    # ------------------------------------------------------------------
    print("\n--- A. EXHAUSTIVE EPISTEMIC TRICHOTOMY ---")
    profiles = list(product((0, 1), repeat=2))
    worlds: List[World] = [(p, q) for p in profiles for q in profiles]
    assert len(worlds) == 16

    n_sets = 0
    n_dist = n_eq = n_unknown = 0
    rsep_implies_dist = True
    found_dist_without_rsep = None
    found_unknown = None

    # Enumerate every non-empty subset of the 16 possible worlds.
    for bits in range(1, 1 << len(worlds)):
        ws = [worlds[i] for i in range(len(worlds)) if bits & (1 << i)]
        n_sets += 1
        st = status(ws)
        if st == "DIST":
            n_dist += 1
        elif st == "EQ":
            n_eq += 1
        else:
            n_unknown += 1
            if found_unknown is None:
                found_unknown = ws

        if rsep(ws) and not dist(ws):
            rsep_implies_dist = False
        if dist(ws) and not rsep(ws) and found_dist_without_rsep is None:
            found_dist_without_rsep = ws

    chk("A1 all 65,535 nonempty compatible-world sets classified",
        n_sets == 65535, n_sets)
    chk("A2 trichotomy contains genuine DIST cases", n_dist > 0, n_dist)
    chk("A3 trichotomy contains genuine EQ cases", n_eq > 0, n_eq)
    chk("A4 trichotomy contains genuine UNKNOWN cases", n_unknown > 0, n_unknown)
    chk("A5 robust separator always implies warranted distinguishability",
        rsep_implies_dist)
    chk("A6 quantifier-order trap exists: DIST without one common robust separator",
        found_dist_without_rsep is not None,
        str(found_dist_without_rsep))
    chk("A7 non-separation can remain UNKNOWN rather than MERGE",
        found_unknown is not None,
        str(found_unknown))

    # Explicit quantifier witness:
    # world 1 separated only by s0; world 2 separated only by s1.
    quantifier_trap: List[World] = [
        ((0, 0), (1, 0)),
        ((0, 0), (0, 1)),
    ]
    chk("A8 forall-world exists-separator is DIST",
        dist(quantifier_trap) and status(quantifier_trap) == "DIST")
    chk("A9 no exists-one-separator forall-world witness in quantifier trap",
        not rsep(quantifier_trap))
    # Wrong simplification would fail here.
    wrong_rsep_only_status = "DIST" if rsep(quantifier_trap) else "UNKNOWN"
    chk("A10 RSEP-only rival is falsified by quantifier trap",
        wrong_rsep_only_status != status(quantifier_trap),
        f"rival={wrong_rsep_only_status} correct={status(quantifier_trap)}")

    # Unknown witness: one compatible world equal, one distinguishable.
    unknown_trap: List[World] = [
        ((0, 0), (0, 0)),
        ((0, 0), (1, 0)),
    ]
    chk("A11 mixed compatible worlds force UNKNOWN",
        status(unknown_trap) == "UNKNOWN")
    wrong_binary = "MERGE" if not rsep(unknown_trap) else "SPLIT"
    chk("A12 binary no-separator=>merge rival is falsified",
        wrong_binary == "MERGE" and correction(False, status(unknown_trap)) == "DO_NOT_YET_DECIDE")

    # Derived directions.
    chk("A13 merged present + DIST => SPLIT",
        correction(True, "DIST") == "SPLIT")
    chk("A14 distinguished present + EQ => MERGE",
        correction(False, "EQ") == "MERGE")
    chk("A15 UNKNOWN never forces split or merge",
        correction(True, "UNKNOWN") == "DO_NOT_YET_DECIDE"
        and correction(False, "UNKNOWN") == "DO_NOT_YET_DECIDE")

    # ------------------------------------------------------------------
    # B. Exhaustive joint-sufficiency / atomic-ablation attack.
    # ------------------------------------------------------------------
    print("\n--- B. EXHAUSTIVE JOINT-SUFFICIENCY CONFIGURATION TEST ---")
    n_functions = 0
    all_frontiers_minimal = True
    synergy_witness = None
    nonunique_witness = None

    full = frozenset(FEATURES)
    for mask in range(1 << (1 << len(FEATURES))):  # 256 Boolean functions
        n_functions += 1
        front = frontier_for(mask, 1)

        # Every returned sufficient config must be subset-minimal.
        for cfg in front:
            if truth_value(mask, cfg) != 1:
                all_frontiers_minimal = False
            if any(other < cfg and truth_value(mask, other) == 1 for other in CONFIGS):
                all_frontiers_minimal = False

        if len(front) > 1 and nonunique_witness is None:
            nonunique_witness = (mask, front)

        if truth_value(mask, full) == 1:
            singles_harmless = all(
                truth_value(mask, full - {f}) == 1 for f in FEATURES
            )
            # Need some joint contraction to fail.
            joint_failure = any(
                truth_value(mask, cfg) == 0
                for cfg in CONFIGS
                if len(cfg) <= 1
            )
            if singles_harmless and joint_failure and synergy_witness is None:
                synergy_witness = (mask, frontier_for(mask, 1), atomic_indispensable_from_full(mask))

    chk("B1 all 256 Boolean consequence functions enumerated",
        n_functions == 256)
    chk("B2 every realization frontier is genuinely subset-minimal",
        all_frontiers_minimal)
    chk("B3 incomparable-minimum functions exist",
        nonunique_witness is not None,
        str(nonunique_witness))
    chk("B4 non-additive joint-necessity witness exists",
        synergy_witness is not None,
        str(synergy_witness))

    mask, front, atomic = synergy_witness
    chk("B5 synergy witness has zero individually indispensable features at full present",
        len(atomic) == 0,
        f"atomic={sorted(atomic)} frontier={list(map(sorted, front))}")
    chk("B6 nevertheless the jointly sufficient frontier is nonempty",
        len(front) > 0)
    # Wrong atomic rule would retain no structure.
    wrong_atomic_cfg = frozenset(atomic)
    chk("B7 atomic-indispensability rival loses protected consequence",
        truth_value(mask, wrong_atomic_cfg) == 0,
        f"wrong_cfg={sorted(wrong_atomic_cfg)}")

    # Canonical explicit OR-style witness on a,b; c irrelevant.
    # value 1 iff a or b is present.
    or_mask = 0
    for cfg in CONFIGS:
        if "a" in cfg or "b" in cfg:
            or_mask |= 1 << config_index(cfg)
    or_front = frontier_for(or_mask, 1)
    chk("B8 explicit joint frontier preserves two incomparable minima",
        or_front == frozenset({frozenset({"a"}), frozenset({"b"})}),
        str(list(map(sorted, or_front))))

    # ------------------------------------------------------------------
    # C. Dynamic quotient coherence.
    # ------------------------------------------------------------------
    print("\n--- C. RIGHT-CONGRUENCE ATTACK ---")
    descriptive_eq, extension_preserves = right_congruence_counterexample()
    chk("C1 shallow descriptive equivalence can hold",
        descriptive_eq)
    chk("C2 authorized extension can break that equivalence",
        not extension_preserves)
    chk("C3 therefore descriptive quotient is not automatically executable state",
        descriptive_eq and not extension_preserves)

    # ------------------------------------------------------------------
    # D. Ground vs preference.
    # ------------------------------------------------------------------
    print("\n--- D. GROUND / PREFERENCE SEPARATION ---")
    candidates = [
        {"name": "cheap_invalid", "ground_ok": False, "cost": 0},
        {"name": "valid_expensive", "ground_ok": True, "cost": 10},
        {"name": "valid_cheaper", "ground_ok": True, "cost": 3},
    ]
    chosen = lawful_min(candidates)
    chk("D1 unlawful cheapest candidate cannot win by economy",
        chosen == ["valid_cheaper"], chosen)

    equivalent_valid = [
        {"name": "same_semantics_high_cost", "ground_ok": True, "cost": 9},
        {"name": "same_semantics_low_cost", "ground_ok": True, "cost": 2},
    ]
    chosen2 = lawful_min(equivalent_valid)
    chk("D2 preference can distinguish semantically lawful equivalents",
        chosen2 == ["same_semantics_low_cost"], chosen2)
    chk("D3 semantics-only rival is incomplete for developmental choice",
        len(equivalent_valid) == 2 and len(chosen2) == 1)

    # ------------------------------------------------------------------
    # E. Self-application.
    # ------------------------------------------------------------------
    print("\n--- E. SELF-APPLICATION WITHOUT A META-LAW ---")
    # Treat continuation-generating mechanisms exactly as candidate presents.
    method_worlds: List[World] = [
        # On probe s0, m1 and m2 differ; on s1 they agree.
        ((1, 0), (0, 0)),
    ]
    method_eq_worlds: List[World] = [
        ((1, 1), (1, 1)),
        ((0, 0), (0, 0)),
    ]
    chk("E1 developmental mechanisms can be consequentially distinguished by same relation",
        status(method_worlds) == "DIST")
    chk("E2 developmental mechanisms can also be warranted equivalent",
        status(method_eq_worlds) == "EQ")

    # ------------------------------------------------------------------
    # Synthesis / falsifiers.
    # ------------------------------------------------------------------
    print("\n--- SYNTHESIS ---")
    print(f"world-set counts: DIST={n_dist} EQ={n_eq} UNKNOWN={n_unknown}")
    print("wrong simplifications explicitly defeated:")
    print("  - exists-one-separator/forall-world as definition of distinguishability")
    print("  - no robust separator => merge")
    print("  - atomic individual indispensability")
    print("  - executable state without right congruence")
    print("  - cheapest candidate regardless of semantic ground")
    print("  - semantic equivalence as complete developmental preference")

    n_pass = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    verdict = "PASS" if n_pass == total else "FAIL"

    print("\n" + "=" * 100)
    print(f"VERDICT: {verdict} {n_pass}/{total}")
    if verdict == "PASS":
        print("VERIFIED_WCD_V1_EPISTEMIC_TRICHOTOMY_EXHAUSTIVE")
        print("VERIFIED_WCD_V1_QUANTIFIER_ORDER")
        print("VERIFIED_WCD_V1_JOINT_CONFIGURATION_MINIMALITY_EXHAUSTIVE")
        print("VERIFIED_WCD_V1_RIGHT_CONGRUENCE_NECESSITY_FOR_EXECUTABLE_QUOTIENT")
        print("VERIFIED_WCD_V1_GROUND_MEASURE_PREFERENCE_SEPARATION")
        print("VERIFIED_WCD_V1_SELF_APPLICATION_CLOSURE")
        print("SURVIVED_DEDICATED_FALSIFICATION_SUITE_WARRANTED_CONSEQUENTIAL_DIFFERENCE_V1")
    else:
        print("FALSIFIED_OR_BROKEN_WARRANTED_CONSEQUENTIAL_DIFFERENCE_V1")
        for name, ok, detail in checks:
            if not ok:
                print("FAILED:", name, detail)
        raise SystemExit(1)


if __name__ == "__main__":
    run()

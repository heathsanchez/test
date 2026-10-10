"""V168: independent arithmetic replay of source-qualified adaptive future-class ledgers.

The compiled C++ algorithm emits EXACT original source and independent
meeting clocks. This Python program independently replays all effective
ledger edges for selected complete finite cutoffs, reconstructs
component membership WITHOUT trusting the C++ union-find, and verifies
terminal proof propagation through the resulting undirected graph.

Large cutoffs up to 2^24 are source-exact *executable* C++ results,
not millions of individually Lean-reified theorem declarations. The
Lean module formally checks the abstract order-independent closure.

The G7 negative control has a disjoint positive cycle and MUST stay
uncertified relative to the chosen 7<->14 terminal class.

All finite source cutoffs remain separate from universal Collatz QED.
"""
from __future__ import annotations

import json
import hashlib
import subprocess
from collections import Counter
from pathlib import Path
from typing import Callable


def T(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3*n+1) // 2


def G(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3*n+7) // 2


def follow(n: int, t: int, step: Callable[[int],int]) -> int:
    assert n > 0 and t >= 0
    for _ in range(t):
        n = step(n)
        assert n > 0
    return n


class IndependentUnion:
    def __init__(self, N: int):
        self.parent = list(range(N+1))
        self.weight = [1]*(N+1)
        self.good = bytearray(N+1)

    def root(self, n: int) -> int:
        r = n
        while r != self.parent[r]:
            r = self.parent[r]
        while n != self.parent[n]:
            y = self.parent[n]
            self.parent[n] = r
            n = y
        return r

    def unite(self, a: int, b: int):
        a, b = self.root(a), self.root(b)
        if a == b:
            return
        if self.weight[a] < self.weight[b]:
            a, b = b, a
        self.parent[b] = a
        self.weight[a] += self.weight[b]
        self.good[a] |= self.good[b]

    def mark(self, n: int):
        self.good[self.root(n)] = 1

    def snapshot(self, N: int):
        minimum = {}
        weights = Counter()
        for n in range(1, N+1):
            r = self.root(n)
            minimum[r] = min(minimum.get(r, n), n)
            weights[r] += 1
        pending = sorted(
            [(minimum[r], x) for r, x in weights.items() if not self.good[r]],
            key=lambda p: (-p[1], p[0])
        )
        return {
            "unknown_sources": sum(n for _, n in pending),
            "unknown_components": len(pending),
            "largest": max((x for _,x in pending), default=0),
            "good_components": sum(1 for r in weights if self.good[r]),
            "top_components": [list(x) for x in pending[:15]],
            "all_positive_source_count": sum(weights.values()),
        }


def verify_full_receipt(path: Path, summary: dict):
    k = summary["k"]
    N = (1 << k) - 1
    step = T if summary["map"] == "TRUE_COLLATZ" else G
    roots = (1,2) if step == T else (7,14)
    union = IndependentUnion(N)
    record_count = Counter()
    snapshot = None
    seen_seed = False
    phase = "initial"
    for line in path.read_text().splitlines():
        rec = json.loads(line)
        kind = rec["type"]
        record_count[kind] += 1
        if kind == "seed":
            assert not seen_seed
            seen_seed = True
            n, p = rec["source"], rec["other"]
            i, j = rec["clock"], rec["other_clock"]
            assert (n,p) == roots
            assert follow(n,i,step) == follow(p,j,step)
            union.unite(n,p)
            union.mark(n)
        elif kind == "merge":
            n, p = rec["source"], rec["other"]
            i, j = rec["clock"], rec["other_clock"]
            x = rec["endpoint"]
            assert 0 < n <= N and 0 < p <= N and n != p
            assert i >= 0 and j >= 0 and i <= summary["owner_clock_cap"]
            assert j <= summary["owner_clock_cap"]
            assert follow(n, i, step) == x
            assert follow(p, j, step) == x
            union.unite(n,p)
        elif kind == "terminal":
            n, i, x = rec["source"], rec["clock"], rec["endpoint"]
            assert 0 < n <= N and x in roots
            assert follow(n,i,step) == x
            union.unite(n,x)
            union.mark(n)
        elif kind == "cycle":
            assert step == G
            n, i, j = rec["source"], rec["clock"], rec["earlier_clock"]
            x = rec["endpoint"]
            assert 0 < n <= N and 0 <= j < i
            assert follow(n,i,step) == follow(n,j,step) == x
            assert x not in roots
        elif kind == "phase":
            assert rec == {"type":"phase","name":"after_initial"}
            assert phase == "initial"
            phase = "adaptive"
            snapshot = union.snapshot(N)
        else:
            raise AssertionError(("unexpected receipt type", rec))
    assert seen_seed and phase == "adaptive"
    assert snapshot is not None
    final = union.snapshot(N)
    for result, prefix in ((snapshot, "initial"), (final, "final")):
        assert result["all_positive_source_count"] == N
        assert result["unknown_sources"] == summary[f"{prefix}_unresolved_sources"]
        assert result["unknown_components"] == summary[f"{prefix}_unresolved_components"]
        assert result["largest"] == summary[f"{prefix}_largest_unresolved_component"]
        assert result["good_components"] == summary[f"{prefix}_good_components"]
        assert result["top_components"] == summary[f"{prefix}_top_components"]

    # A complete certificate assertion is additionally checked by
    # independent direct actual-orbit replay when N<=2^14-1.
    direct_crosschecks = 0
    for n in range(1,N+1):
        if union.good[union.root(n)]:
            x = n
            for t in range(701):
                if x in roots:
                    break
                x = step(x)
            else:
                raise AssertionError(("false terminal class reported", n))
            direct_crosschecks += 1
    if step == G:
        assert not union.good[union.root(1)]
        assert not union.good[union.root(5)]
        assert not union.good[union.root(11)]
        assert not union.good[union.root(20)]
        assert not union.good[union.root(10)]
    return {
        "source_cutoff": N,
        "verified_receipts": sum(record_count.values()),
        "receipt_types": dict(record_count),
        "independently_directly_verified_members": direct_crosschecks,
        "initial": snapshot,
        "final": final,
        "synthetic_negative_preserved": step != G or not union.good[union.root(1)],
        "two_real_clocks_replayed": True,
        "source_zero_absent": True
    }


def compile_program(workdir: Path):
    source = Path("research/collatz_v168_retrospective_quotient.cpp")
    assert source.is_file(), source
    executable = workdir / "collatz_v168_quotient"
    subprocess.run(
        ["g++", "-O3", "-std=c++17", str(source), "-o", str(executable)],
        check=True
    )
    return executable


def run_case(executable: Path, evidence: Path, k: int,
             H: int, A: int, name: str, receipts: bool = False):
    stem = f"v168_{name}_k{k}_H{H}_A{A}"
    receipt = evidence / f"{stem}.jsonl"
    args = [str(executable), str(k), str(H), str(A), name]
    if receipts:
        args.append(str(receipt))
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    summary = json.loads(result.stdout)
    assert summary["schema"] == "COLLATZ_V168_RETROACTIVE_FUTURE_QUOTIENT"
    assert summary["map"] == ("TRUE_COLLATZ" if name == "T" else "G7_SYNTHETIC")
    assert summary["positive_source_cutoff"] == 2**k-1
    assert summary["initial_unresolved_sources"] >= summary["final_unresolved_sources"]
    assert summary["initial_unresolved_components"] >= summary["final_unresolved_components"]
    assert summary["finite_certificate_coverage_only"]
    assert summary["global_collatz"] == "UNKNOWN"
    assert summary["qed"] is False
    path = evidence / f"{stem}.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n")
    return summary, receipt if receipts else None


def main():
    evidence = Path("evidence")
    evidence.mkdir(parents=True, exist_ok=True)
    exe = compile_program(evidence)
    true_cases = [
        (8,32,300),(10,40,300),(12,48,300),(14,56,300),
        (16,64,350),(18,72,400),(20,80,400),(22,88,500),(24,96,600)
    ]
    rows = []
    independent_receipts = []
    for k,H,A in true_cases:
        value, receipt = run_case(exe, evidence, k,H,A,"T", receipts=k in (10,12,14))
        rows.append(value)
        if receipt is not None:
            independent_receipts.append(
                verify_full_receipt(receipt,value)
            )

    controls = []
    for k,H,A in [(12,48,300),(20,80,400)]:
        value,receipt = run_case(exe,evidence,k,H,A,"G",receipts=k==12)
        controls.append(value)
        if receipt is not None:
            independent_receipts.append(
                verify_full_receipt(receipt,value)
            )

    exact = {x["k"]:x for x in rows}
    assert [(exact[k]["initial_unresolved_sources"],
             exact[k]["initial_unresolved_components"]) for k in
            (8,10,12,14,16,18,20,22,24)] == [
             (0,0),(2,1),(16,1),(5,2),(41,12),
             (181,26),(365,75),(1477,236),(4815,649)]
    assert all(x["final_unresolved_sources"]==0 for x in rows)
    assert all(x["final_unresolved_components"]==0 for x in rows)
    assert all(x["final_good_components"]==1 for x in rows)
    assert [(exact[k]["additional_owner_attempts"],
             exact[k]["additional_source_clock_steps"],
             exact[k]["additional_actual_two_clock_mergers"]) for k in
            (18,20,22,24)] == [
             (26,522,26),(75,1862,75),(236,5842,236),(649,16606,649)]
    assert all(x["additional_direct_terminal_hits"]==0 for x in rows)
    assert all(x["observed_nonterminal_cycle_receipts"]==0 for x in rows)

    g = controls[-1]
    assert g["initial_unresolved_sources"]==898855
    assert g["initial_unresolved_components"]==82
    assert g["final_unresolved_sources"]==898779
    assert g["final_unresolved_components"]==1
    assert g["final_largest_unresolved_component"]==898779
    assert g["observed_nonterminal_cycle_receipts"]==70
    assert g["final_good_components"]==1

    # A fixed contraction factor 0.8 with zero additive error
    # fails on an actual finite source-window cohort.
    mass_ratio_20_22 = (
        exact[22]["initial_unresolved_sources"] / (2**22)
    ) / (exact[20]["initial_unresolved_sources"] / (2**20))
    assert mass_ratio_20_22 > 1.0

    # V167's published source-ordered J=12 policy has a DIFFERENT
    # earlier-source clock budget; the comparison is operational,
    # not a controlled one-variable causal ablation.
    prior_v167_k20_timeout = 1050
    assert exact[20]["initial_unresolved_sources"] < prior_v167_k20_timeout

    source_bytes = Path("research/collatz_v168_retrospective_quotient.cpp").read_bytes()
    return {
        "schema":"COLLATZ_V168_UNION_FIRST_ADAPTIVE_FUTURE_CLASS_AUDIT",
        "program_sha256":hashlib.sha256(source_bytes).hexdigest(),
        "exact_shortcut_natural_source_positive":True,
        "two_independent_actual_clocks_for_each_meeting":True,
        "transitive_certificate_transfer_formally_separate":True,
        "all_tested_true_populations_finitely_certified":True,
        "highest_true_tested_positive_source":2**24-1,
        "true_complete_population_largest_k":24,
        "true_k20_initial_unknown":365,
        "true_k20_initial_component_count":75,
        "true_k20_additional_merge_certificates":75,
        "true_k20_additional_source_clock_steps":1862,
        "true_k24_initial_unknown":4815,
        "true_k24_initial_component_count":649,
        "true_k24_additional_merge_certificates":649,
        "true_k24_additional_source_clock_steps":16606,
        "true_k24_final_unknown":0,
        "initial_mass_ratio_k20_to_k22":mass_ratio_20_22,
        "naive_zero_error_lambda_point8_dyadic_contraction_falsified":True,
        "v167_comparison_prior_J12_timeouts":prior_v167_k20_timeout,
        "v168_earlier_source_clock_budget_not_matched_to_v167":True,
        "independent_receipt_replays":independent_receipts,
        "true_rows":rows,
        "synthetic_G7_controls":controls,
        "bounded_timeout_is_NOT_a_nonconvergence_proof":True,
        "no_primitive_root_assumption":True,
        "no_external_density_theorem_used":True,
        "V151_sparse_exceptional_mass_theorem_proved":False,
        "global_all_positive_source_closure_proved":False,
        "global_collatz":"UNKNOWN",
        "qed":False
    }


if __name__ == "__main__":
    result = main()
    Path("evidence/v168-summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n"
    )
    print(json.dumps({
        "schema":result["schema"],
        "max_source":result["highest_true_tested_positive_source"],
        "k20_new_merges":result["true_k20_additional_merge_certificates"],
        "k24_new_merges":result["true_k24_additional_merge_certificates"],
        "k24_final_unknown":result["true_k24_final_unknown"],
        "g7_remaining":result["synthetic_G7_controls"][-1]["final_unresolved_sources"],
        "global_collatz":result["global_collatz"]
    }, sort_keys=True))

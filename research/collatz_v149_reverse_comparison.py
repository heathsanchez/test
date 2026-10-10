"""V149 — constructive protected-future reverse source comparisons.

Discover earlier positive sources by enumerating ONLY actual shortcut
inverse edges from a true forward endpoint. Every proposed proof is
replayed under exact Nat arithmetic, stores both independent clocks,
and is admitted only if 0 < p < original n.

A candidate with a smaller source dominates one with a larger source
ONLY when they share the same exact target endpoint and the protected
question is existence of a lower positive source, not proof cost or
other future observations.

Finite failure to discover any admissible inverse word is UNKNOWN.
Collatz is not proved or refuted by the bounded search.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json


def shortcut(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2


def forward(n: int, i: int) -> int:
    x = n
    for _ in range(i):
        x = shortcut(x)
    return x


@dataclass(frozen=True)
class ReverseCertificate:
    source: int
    back_clock: int
    path: tuple[int, ...]

    def replay(self, target: int) -> bool:
        return (
            self.source > 0
            and self.path[0] == self.source
            and self.path[-1] == target
            and self.back_clock == len(self.path) - 1
            and all(shortcut(x) == z
                    for x, z in zip(self.path, self.path[1:]))
        )


def local_inverse_candidates(y: int) -> list[int]:
    assert y > 0
    candidates = [2 * y]
    num = 2 * y - 1
    if num % 3 == 0:
        p = num // 3
        if p > 0 and p % 2 == 1:
            candidates.append(p)
    assert all(shortcut(p) == y for p in candidates)
    assert len(set(candidates)) == len(candidates)
    return candidates


def inverse_bfs(y: int, max_depth: int, max_records: int = 50000):
    assert y > 0 and max_depth >= 0
    current = [ReverseCertificate(y, 0, (y,))]
    all_records = current[:]
    for depth in range(1, max_depth + 1):
        nxt = []
        for rec in current:
            for p in local_inverse_candidates(rec.source):
                new = ReverseCertificate(p, depth, (p,) + rec.path)
                assert new.replay(y)
                nxt.append(new)
                if len(all_records) + len(nxt) > max_records:
                    raise RuntimeError("bounded reverse budget exhausted")
        current = nxt
        all_records.extend(nxt)
    assert all(r.replay(y) for r in all_records)
    return all_records


def compare(original: int, forward_clock: int, reverse_depth: int):
    assert original > 0
    y = forward(original, forward_clock)
    recs = inverse_bfs(y, reverse_depth)
    accepted = [r for r in recs if 0 < r.source < original]
    for r in accepted:
        assert forward(r.source, r.back_clock) == y
        assert forward(original, forward_clock) == y
        for suffix in (0, 1, 2, 3, 7, 13, 24):
            assert (forward(original, forward_clock + suffix)
                    == forward(r.source, r.back_clock + suffix))
    # Dominance is only within the EXACT SAME endpoint; it does not
    # delete clocks before replaying their actual semantic consequences.
    best_by_source = {}
    for r in sorted(accepted, key=lambda z: (z.source, z.back_clock, z.path)):
        best_by_source.setdefault(r.source, r)
    smallest = min(accepted, key=lambda r:(r.source,r.back_clock)) if accepted else None
    if smallest:
        assert all(smallest.source <= c.source for c in accepted)
    return {
        "original_source": original,
        "forward_clock": forward_clock,
        "true_endpoint": y,
        "reverse_depth_checked": reverse_depth,
        "reverse_certificates_checked": len(recs),
        "admissible_candidates": len(accepted),
        "positive_source_cap": original,
        "status": "WARRANTED_FINITE_LOWER_MERGER" if smallest else "UNKNOWN_REVERSE_DEPTH_LIMIT",
        "selected": {
            "lower_source":smallest.source,
            "independent_back_clock":smallest.back_clock,
            "reverse_path":list(smallest.path)
        } if smallest else None,
        "clock_preserved": True,
        "no_available_lower_source_claimed": False
    }


def render_semantic_controls():
    examples={}
    for label, source, clock, depth in (
        ("V128_source21_preferred_root_repaired",21,3,5),
        ("V106_ascending_sign_source9_repaired",9,6,5),
        ("V140_source5_valid_asymmetric_clocks",5,1,5),
        ("V129_even_source6_zero_reverse_clock",6,1,5),
        ("V146_source27_short_prefix_unknown",27,3,12),
        ("V148_terminal_source1_no_smaller_positive",1,1,12),
        ("V139_source27_later_descent_admitted",27,59,0),
    ):
        examples[label]=compare(source,clock,depth)

    assert examples["V128_source21_preferred_root_repaired"]["status"] == "WARRANTED_FINITE_LOWER_MERGER"
    ex=examples["V128_source21_preferred_root_repaired"]
    candidates=inverse_bfs(ex["true_endpoint"],5)
    root3=[r for r in candidates if r.source==3 and r.back_clock==2]
    assert any(r.path==(3,5,8) for r in root3)
    assert all(r.replay(8) for r in root3)
    # The smallest reverse source at depth<=5 could be p1, so do not
    # confuse selected source with a protected named root certificate.

    assert examples["V106_ascending_sign_source9_repaired"]["status"] == "WARRANTED_FINITE_LOWER_MERGER"
    cands=inverse_bfs(13,5)
    assert any(r.path==(7,11,17,26,13) and r.source==7 and r.back_clock==4
               for r in cands)

    assert examples["V146_source27_short_prefix_unknown"]["status"]=="UNKNOWN_REVERSE_DEPTH_LIMIT"
    assert examples["V146_source27_short_prefix_unknown"]["true_endpoint"]==31
    assert examples["V139_source27_later_descent_admitted"]["selected"]["lower_source"]==23
    assert examples["V139_source27_later_descent_admitted"]["true_endpoint"]==23
    assert examples["V148_terminal_source1_no_smaller_positive"]["status"]=="UNKNOWN_REVERSE_DEPTH_LIMIT"
    assert examples["V129_even_source6_zero_reverse_clock"]["selected"] is not None

    # At a single endpoint y>=n a totally comparable pure-even reverse
    # chain can grow forever without providing ANY smaller source.
    pure_even_no_go=[]
    for n,y in ((1,2),(27,31),(21,22)):
        assert n<=y
        for j in range(70):
            p=(1<<j)*y
            assert p>=n
            assert forward(p,j)==y
            assert p<=2*p
        pure_even_no_go.append({"original_source":n,"target_endpoint":y,
                                "comparable_reverse_depths":70,
                                "all_sources_at_least_original":True})

    # The V147 static ratio quotient is not a transition bisimulation:
    # equal (9,13)~(27,39), but unscaled +1 even updates differ.
    assert 27*13==9*39
    assert 27*14!=9*40

    # V106's opposite sign return patterns must not get converted into
    # a universal monotone rank claim.
    v106_signs=[
        dict(initial=5, clock=4, path=[5,8,4,2,1],
             guard="source-capped descent"),
        dict(initial=9, clock=6, path=[9,14,7,11,17,26,13],
             guard="positive ascending actual return")
    ]
    for rec in v106_signs:
        actual=[rec["initial"]]
        for k in range(rec["clock"]):
            actual.append(shortcut(actual[-1]))
        assert actual==rec["path"]

    return examples,pure_even_no_go,v106_signs


def main():
    examples,chain_controls,sign_controls=render_semantic_controls()
    # Finite additional discoverability audit. Each source is
    # investigated with one shallow genuine forward endpoint, not
    # declared a theorem covering all starts.
    statuses=[]
    for source in range(2,151):
        a=compare(source,3,4)
        statuses.append(a["status"])
    passed=sum(x=="WARRANTED_FINITE_LOWER_MERGER" for x in statuses)
    unresolved=len(statuses)-passed
    assert unresolved>=0
    return {
       "schema":"COLLATZ_V149_SOURCE_RELATIVE_REVERSE_COMPARISON",
       "exact_semantic_controls":examples,
       "pure_even_wqo_falsifier":chain_controls,
       "both_V106_return_signs_protected":sign_controls,
       "frozen_static_quotient_future_counterexample":{
            "equivalent_before":True,"equivalent_after_unscaled_even_update":False
       },
       "shallow_true_source_comparisons_checked":len(statuses),
       "admitted_shallow_cases":passed,
       "unknown_shallow_cases":unresolved,
       "every_admitted_certificate_has_two_exact_real_clocks":True,
       "finite_unknown_means_divergence":False,
       "comparison_order_alone_produces_source_cap":False,
       "all_no_exit_streams_comparison_complete":False,
       "universal_collatz":"UNKNOWN",
       "qed":False
    }


if __name__=="__main__":
    print(json.dumps(main(),indent=2,sort_keys=True))

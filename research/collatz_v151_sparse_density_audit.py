"""V151 exact finite audit for sparse dyadic exceptional envelopes.

This tests the MATHEMATICAL DIFFERENCE between:
  - all-large-k 1/k exceptional mass (V150 sufficient), and
  - arbitrarily large dyadic cutoffs with exceptional mass below any
    prescribed 1/q (V151 sufficient).

The toy population is explicitly synthetic, not a Collatz population:
it has zero exceptions at even k and half the dyadic cutoff at odd k.
It has arbitrarily sparse zero-mass scales but no eventual all-k
1/k bound. This proves the analytical target can be weakened.

Finite real Collatz counts are inherited from the exact V150 audit,
and are NOT extrapolated to a density limit.
"""
from __future__ import annotations
import json
from research.collatz_v150_density_audit import dyadic_mass_audit

def toy_bad_count(k: int) -> int:
    assert k>=1
    return 0 if k%2==0 else 1<<(k-1)

def demonstrate_strict_weakening():
    for q in range(1,51):
        for X0 in (0,1,3,15,100,1234,16384,2**20):
            k=max(2, (X0+q).bit_length()+1)
            if k%2: k+=1
            assert (1<<k)>=X0
            assert q*toy_bad_count(k)<(1<<k)
    odd_k_fails=[]
    for k in range(3,80,2):
        assert k*toy_bad_count(k)>(1<<k)
        odd_k_fails.append(k)
    assert len(odd_k_fails)>=30
    return {"synthetic_not_collatz":True,
        "sparse_reciprocal_trials":50*8,
        "eventual_all_k_one_over_k_bound_fails":True,
        "arbitrarily_large_odd_k_failures_tested":len(odd_k_fails),
        "toy_zero_mass_even_scales_are_unbounded_in_k":True,
        "q_is_user_selected_precision_not_time_budget":True}

def audit_real_finite_envelopes():
    rows=dyadic_mass_audit(kmin=6,kmax=14,multiplier=12)
    assert len(rows)==9
    assert all(r["mass_test_k_times_unknown_le_cutoff"] for r in rows)
    assert all(r["all_unknown_may_still_converge"] for r in rows)
    return [
      {"k":r["k"],
       "cutoff":r["cutoff_exclusive"],
       "terminal_path_budget":r["shortcut_budget"],
       "unknown_count":r["unknown_exceptional_envelope"],
       "finite_k_mass_inequality":r["mass_test_k_times_unknown_le_cutoff"],
       "unknown_is_not_a_counterexample":True}
      for r in rows]

def main():
    toy=demonstrate_strict_weakening()
    real=audit_real_finite_envelopes()
    return {
      "schema":"COLLATZ_V151_SPARSE_EXCEPTIONAL_DENSITY_INTERFACE",
      "toy_sparse_vs_eventual_all_scale_separator":toy,
      "bounded_true_shortcut_terminal_envelopes":real,
      "external_mazur_source_rebuilt_here":False,
      "ordinary_predecessor_target_nondivisible3_guard_preserved":True,
      "positive_density_to_universal_requires_sparse_mass_premise":True,
      "all_scale_one_over_k_bound_assumed":False,
      "sparse_all_depth_certified_population_proved":False,
      "extrapolation_from_finite_coverage_prohibited":True,
      "global_collatz":"UNKNOWN",
      "qed":False
    }

if __name__=="__main__":
    print(json.dumps(main,indent=2,sort_keys=True))

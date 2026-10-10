"""V166 executable finite-clock source/endpoint certificate mass audit.

Each original source n = r + 2^k*q is present, exactly once. Its real
T^(k+h) endpoint agrees with the source-typed ternary chart's T^h
endpoint from g + 3^a*q. Hit-at-clock k+h is equivalent to hit-by-
clock k+h because terminal {1,2} is forward-invariant.

The finite certificate populations are therefore exact; they do NOT
establish any asymptotic loss of UNKNOWN sources. Adverse all-ones
and long-clock source fibers are preserved.

V133's existing all-offset source23->earlier source3 family is also
replayed as a genuine two-clock source-capped certificate. This is
proof reuse, not a new universality claim.
"""
from __future__ import annotations
import json
from collections import Counter


def T(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2


def source_chart(n:int,k:int):
    a=0
    for _ in range(k):
        a+=n%2
        n=T(n)
    return a,n


def advance(n:int,t:int):
    for _ in range(t):
        n=T(n)
    return n


def terminal(n:int)->bool:
    return n==1 or n==2


def main():
    Q=64
    total_real_cases=0
    source0_timeouts=0
    root23_reused=0
    rows=[]
    worst_fibers=[]
    for k in range(0,10):
        h_scales=tuple(sorted(set((0,k,2*k,4*k,8*k))))
        for h in h_scales:
            max_unknown=-1
            max_residue=None
            source_terminal=0
            source_unresolved=0
            num_fully_unresolved=0
            for r in range(1<<k):
                a,g=source_chart(r,k)
                source_hits=0
                endpoint_hits=0
                for q in range(Q):
                    n=r+(1<<k)*q
                    y=g+(3**a)*q
                    e=advance(n,k+h)
                    v=advance(y,h)
                    assert e==v,(k,h,r,q,n,y,e,v)
                    source_hit=terminal(e)
                    endpoint_hit=terminal(v)
                    assert source_hit==endpoint_hit
                    source_hits+=int(source_hit)
                    endpoint_hits+=int(endpoint_hit)
                    if n==0:
                        assert not source_hit
                        source0_timeouts+=1
                    total_real_cases+=1
                assert source_hits==endpoint_hits
                unknown=Q-source_hits
                if unknown>max_unknown:
                    max_unknown=unknown
                    max_residue=r
                num_fully_unresolved+=int(unknown==Q)
                source_terminal+=source_hits
                source_unresolved+=unknown
            assert source_terminal+source_unresolved==(1<<k)*Q
            rows.append({
                'source_prefix_bits':k,
                'future_clock_budget':h,
                'original_clock_budget':k+h,
                'original_sources_per_prefix':Q,
                'terminal_certified_count':source_terminal,
                'still_unresolved_by_budget_count':source_unresolved,
                'max_unresolved_per_prefix':max_unknown,
                'adversarial_prefix':max_residue,
                'fully_unresolved_prefixes':num_fully_unresolved,
                'full_source_population':(1<<k)*Q,
                'exact_source_and_endpoint_hit_counts_match':True,
            })
            if k in (4,6,8,9) and h in (2*k,8*k):
                worst_fibers.append({
                    'k':k,'h':h,
                    'prefix':max_residue,'timeouts':max_unknown,
                    'Q':Q,'fully_unresolved_prefixes':num_fully_unresolved})
    assert any(z['k']==9 and z['h']==18 and z['timeouts']==64
        for z in worst_fibers)
    assert any(z['k']==9 and z['h']==72 and z['timeouts']==44
        for z in worst_fibers)

    for t in range(0,256):
        n=23+384*t
        p=3+54*t
        assert 0<p<n
        original=advance(n,7)
        earlier=advance(p,1)
        assert original==5+81*t==earlier
        a,g=source_chart(23,7)
        assert (a,g)==(3,5)
        assert original==g+3**a*(3*t)
        root23_reused+=1
    assert root23_reused==256

    return {
        'schema':'COLLATZ_V166_COMPUTABLE_CLOCKED_CERTIFICATE_MASS',
        'actual_map':'even x/2 odd (3x+1)/2',
        'source_population_per_binary_prefix':Q,
        'all_origin_sources_represented_once_per_chart':True,
        'exact_source_endpoint_clock_equality_all_tests':True,
        'actual_finite_hit_count_equality_all_tests':True,
        'real_source_chart_clock_cases':total_real_cases,
        'real_zero_source_cases_preserved_not_certified':source0_timeouts,
        'parametric_root23_join_replayed':root23_reused,
        'root23_independent_clocks':[7,1],
        'root23_all_offset_full_Lean_reused_claim_still_conditional_on_CI':True,
        'worst_fiber_negative_controls':worst_fibers,
        'rows':rows,
        'timeouts_are_not_divergence_proofs':True,
        'same_mass_identity_is_not_contraction':True,
        'source_specific_unbounded_tail_estimate_proved':False,
        'global_terminal_density_one_proved':False,
        'global_collatz':'UNKNOWN','qed':False
    }


if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))

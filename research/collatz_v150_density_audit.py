"""V150 exact density-amplification boundary experiment for MathGraph.

All finite "closed" sources have an actual shortcut trajectory hitting
1 or 2 within an explicit budget. Every source NOT so witnessed remains
UNKNOWN; it is an upper envelope of truly nonconvergent sources over
the specified finite range, not a proof of divergent examples.

The external predecessor theorem is recorded as an EXTERNAL_REPORTED
input, not a locally verified axiom or an unconditional new result.
"""
from __future__ import annotations
import json
from pathlib import Path

def shortcut(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3*n+1)//2

def ordinary(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else 3*n+1

def shortcut_terminal_trace(n: int, budget: int):
    x=n
    path=[x]
    for i in range(budget+1):
        if x in (1,2):
            return path,True
        if i < budget:
            x=shortcut(x)
            path.append(x)
    return path,False

def ordinary_reaches_target(n: int, a: int, H: int):
    x=n
    for k in range(H+1):
        if x==a: return k
        if k<H:
            x=ordinary(x)
    return None

def semantic_separators():
    assert ordinary(1)==4 and shortcut(1)==2
    assert ordinary_reaches_target(1,4,1)==1
    x=1
    for i in range(300):
        assert x in (1,2)
        assert x!=4
        x=shortcut(x)
    cases=[]
    for n in (3,7,15,19,27,31,43,55,63,91,127,255):
        assert n%2==1
        y=shortcut(n)
        assert y%3==2
        assert 2*y==3*n+1
        cases.append({"source":n,"target":y,"target_mod3":2})
    # A strict drop below n is not a terminal certificate:
    p,reach=shortcut_terminal_trace(5,2)
    assert p==[5,8,4] and not reach
    assert p[-1]<5
    # The target-3 exception: only pure even doublings are ordinary
    # predecessors of 3. The exact recurrence is checked below.
    for k in range(1,17):
        X=1<<k
        preds=[]
        for n in range(1,X):
            if ordinary_reaches_target(n,3,20*k) is not None:
                preds.append(n)
        expect=[3*(1<<j) for j in range(k+1) if 3*(1<<j)<X]
        assert preds==expect
    return {"ordinary_start1_visits4_but_shortcut_never_does":True,
            "all_sampled_odd_shortcut_successors_mod3_2":cases,
            "n5_descends_at_clock2_but_no_terminal_certificate":True,
            "target3_only_pure_even_doubling_inverse":True,
            "target3_excluded_from_external_density_theorem":True}

def dyadic_mass_audit(kmin: int=6,kmax: int=14, multiplier:int=12):
    rows=[]
    for k in range(kmin,kmax+1):
        X=1<<k
        H=multiplier*k
        terminal_reached=0
        unknown=[]
        certificates=0
        for n in range(1,X):
            path,good=shortcut_terminal_trace(n,H)
            if good:
                terminal_reached+=1
                assert all(shortcut(a)==b for a,b in zip(path,path[1:]))
                assert path[-1] in (1,2)
                certificates+=1
            else:
                unknown.append(n)
                assert path[-1] not in (1,2)
                assert len(path)==H+1
        assert terminal_reached+len(unknown)==X-1
        count=len(unknown)
        rows.append({
            "k":k, "cutoff_exclusive":X, "shortcut_budget":H,
            "finite_true_terminal_witnesses":terminal_reached,
            "unknown_exceptional_envelope":count,
            "mass_test_k_times_unknown_le_cutoff":(k*count<=X),
            "min_unknown_example":min(unknown) if unknown else None,
            "all_unknown_may_still_converge":True,
            "finite_verified_good_outside_envelope":True,
            "covers_all_positive_n_below_cutoff":True,
        })
    assert any(r["unknown_exceptional_envelope"]>0 for r in rows)
    assert all(r["mass_test_k_times_unknown_le_cutoff"] for r in rows)
    return rows

def predecessor_samples():
    rows=[]
    for k in range(6,14):
        X=1<<k
        H=28*k
        counts={a:0 for a in (1,3,5,7,13)}
        for n in range(1,X):
            x=n
            seen=set()
            for i in range(H+1):
                if x in counts:seen.add(x)
                if x==1:
                    break
                if i<H:
                    x=ordinary(x)
            for t in seen:
                counts[t]+=1
        assert counts[3]==k-1
        assert 0<counts[5] and 0<counts[7] and 0<counts[13]
        assert counts[1]==X-1 # finite check only, not universal proof
        rows.append({"k":k,"cutoff":X,"ordinary_budget":H,
            "finite_ordinary_target_predecessor_lower_counts":counts,
            "external_all_depth_density_inferred":False})
    return rows

def main():
    semantics=semantic_separators()
    mass=dyadic_mass_audit()
    preds=predecessor_samples()
    return {
      "schema":"COLLATZ_V150_SOURCE_ATTACHED_DENSITY_BRIDGE_AUDIT",
      "semantic_guards":semantics,
      "finite_dyadic_terminal_envelopes":mass,
      "finite_predecessor_lower_counts":preds,
      "external_ma zur_theorem_imported_in_local_lean":False,
      "external_positive_lower_density_accepted_only_as_explicit_premise":True,
      "upper_natural_density_one_convergence_proved":False,
      "universal_dyadic_exceptional_mass_bound_proved":False,
      "all_depth_terminal_certificate_cover_proved":False,
      "finite_observation_is_not_density_limit":True,
      "global_collatz":"UNKNOWN",
      "qed":False
    }

if __name__=="__main__":
    print(json.dumps(main(),sort_keys=True,indent=2))

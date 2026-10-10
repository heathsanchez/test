"""V170: eliminate two macroscopic source-attached future classes.

Smallest meaningful observable is L2, the SECOND-largest authentic
two-clock component at original source cutoff 2^k and clock H=8*k.
Unlike the largest UNSEEDED component, this is label-free: terminal
certification is only needed to test which component contains the seed.

The exact C++ ledgers are inherited unchanged from the green V169
branches. The new result is BOUNDED, not an all-scale anti-two-giant
theorem. G5 and G7 retain independent genuine competing basins.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

from research.collatz_v169_clocked_giant_audit import independent_small_full_graph
from research.collatz_v169_c5_component_audit import full_graph as c5_independent

CPP=Path("research/collatz_v168_retrospective_quotient.cpp")
CPP5=Path("research/collatz_v169_c5_component_control.cpp")
EXE=Path("/tmp/v170-binary-ternary-component")
EXE5=Path("/tmp/v170-three-n-plus-five")


def run_c1_c7(k: int,c: int) -> dict:
    assert c in (1,7)
    H=8*k
    d=json.loads(subprocess.check_output(
        [str(EXE),str(k),str(H),str(H),"T" if c==1 else "G"],text=True))
    assert d["schema"]=="COLLATZ_V168_RETROACTIVE_FUTURE_QUOTIENT"
    assert d["initial_good_components"]==1
    assert d["additional_source_clock_steps"]==0
    assert d["final_unresolved_sources"]==d["initial_unresolved_sources"]
    assert d["positive_source_cutoff"] == 2**k-1
    sizes=[d["positive_source_cutoff"]-d["initial_unresolved_sources"]]
    sizes += [n for _,n in d["initial_top_components"]]
    sizes.sort(reverse=True)
    largest, second=(sizes+[0,0])[:2]
    assert largest+sum(sizes[1:])<=2**k-1
    assert second==(sorted(sizes,reverse=True)+[0,0])[1]
    if k<=12:
        indep=independent_small_full_graph(k,c)
        assert indep["unresolved_sources"]==d["initial_unresolved_sources"]
        assert indep["largest_unresolved_component"]==d["initial_largest_unresolved_component"]
    return {
        "k":k,"H":H,"map":f"3n+{c}",
        "source_count":2**k-1,
        "terminal_component_size":d["positive_source_cutoff"]-d["initial_unresolved_sources"],
        "unseeded_component_count":d["initial_unresolved_components"],
        "largest_unseeded_component_size":d["initial_largest_unresolved_component"],
        "first_component_size":largest,
        "second_component_size":second,
        "second_component_fraction_exact":[second,2**k],
        "top_unseeded_minimum_and_size":d["initial_top_components"][:5],
    }


def run_c5(k: int) -> dict:
    H=8*k
    d=json.loads(subprocess.check_output(
        [str(EXE5),str(k),str(H)],text=True))
    assert d["schema"]=="COLLATZ_V169_G5_NON_GCD_COMPONENT_CONTROL"
    assert d["positive_sources"]==2**k-1
    assert d["global_collatz"]=="UNKNOWN" and d["qed"] is False
    good=d["positive_sources"]-d["unseeded_sources"]
    sizes=[good]+[count for _,count in d["top_source_components"]]
    sizes.sort(reverse=True)
    largest,second=(sizes+[0,0])[:2]
    if k<=12:
        indep=c5_independent(k,H)
        assert indep==(d["unseeded_components"],d["unseeded_sources"],
                      d["max_unseeded_component"]),(k,indep,d)
    return {
       "k":k,"H":H,"map":"3n+5",
       "source_count":2**k-1,
       "terminal_component_size":good,
       "unseeded_component_count":d["unseeded_components"],
       "largest_unseeded_component_size":d["max_unseeded_component"],
       "first_component_size":largest,
       "second_component_size":second,
       "second_component_fraction_exact":[second,2**k],
       "top_unseeded_minimum_and_size":d["top_source_components"][:5],
       "seed_cycle":[1,4,2],
       "competing_coprime_cycle_start":187,
    }


def main()->None:
    subprocess.run(["g++","-std=c++17","-O3",str(CPP),"-o",str(EXE)],check=True)
    subprocess.run(["g++","-std=c++17","-O3",str(CPP5),"-o",str(EXE5)],check=True)
    rows=[]
    for k in (8,10,12,14,16,18,20,22,24):
        rows.append(run_c1_c7(k,1))
    for k in (8,12,16,20):
        rows.append(run_c1_c7(k,7))
    for k in (8,12,16,18,20):
        rows.append(run_c5(k))
    bymap={(r["map"],r["k"]):r for r in rows}
    assert bymap["3n+1",20]["second_component_size"]==1
    assert bymap["3n+1",22]["second_component_size"]==2
    assert bymap["3n+1",24]["second_component_size"]==13
    assert bymap["3n+7",20]["second_component_size"]>=140000
    assert bymap["3n+5",20]["second_component_size"]>=140000
    # Strengthened zero-error 2-bit contraction is NOT valid at k22->24:
    # (13/2^24)/(2/2^22) = 13/8 > 1.
    assert 13 * (2**22)> 2 * (2**24)
    out={
      "schema":"COLLATZ_V170_SECOND_LARGEST_FUTURE_COMPONENT",
      "C1_C7_unchanged_cpp_sha256":hashlib.sha256(CPP.read_bytes()).hexdigest(),
      "C5_unchanged_cpp_sha256":hashlib.sha256(CPP5.read_bytes()).hexdigest(),
      "finite_graph_clock":"H(k)=8*k; no adaptive late owner steps",
      "independent_full_graph_checks":["C1,C7 k<=12","C5 k<=12"],
      "conditional_target":"liminf second_component_size/2^k=0",
      "stronger_monotone_contraction_falsified_at_k22_to_k24":True,
      "two_macroscopic_components_survive_under_G5_and_G7":True,
      "every_unknown_stays_UNKNOWN":True,
      "external_timed_density_locally_imported":False,
      "all_scale_sparse_uniqueness_proved":False,
      "global_collatz":"UNKNOWN","qed":False,
      "rows":rows,
    }
    print(json.dumps(out,indent=2,sort_keys=True))


if __name__=="__main__":
    main()

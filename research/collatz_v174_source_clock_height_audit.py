"""V174 — finite original-source giant elimination microscope.

Separate precisely:
  1. Clock increase H=192→200 at SAME source cutoff 2^24.
  2. Height increase 2^24→2^25 at SAME H=200.
  3. Clock increase H=200→240 at SAME cutoff 2^25.

All class labels are actual source-qualified two-clock endpoint unions
obtained by the V172 earliest-owner dominance rule, with V174
original unseeded source extraction. This audit independently replays
every *remaining* source (small residual) to clock H and checks its
relative two-clock component IDs. It also seeks and replays a real
terminal clock for each remaining source up to an explicit finite cap.

Finite terminal clocks are verified facts, not a global convergence
claim. The synthetic one-arrow S5 and G7 controls are never silently
converted to true terminal certificates.

All integer arithmetic is exact. No statistical independence,
asymptotic extrapolation, or finite-to-infinite proof promotion.
"""
from __future__ import annotations
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import subprocess


def T(n: int) -> int:
    return n//2 if n%2==0 else (3*n+1)//2


def generate_executable():
    source=Path("research/collatz_v174_component_identity.cpp")
    assert source.is_file()
    out=Path("evidence/collatz_v174_components")
    out.parent.mkdir(exist_ok=True,parents=True)
    subprocess.run(["g++","-O3","-std=c++17",str(source),"-o",str(out)],check=True)
    return out,hashlib.sha256(source.read_bytes()).hexdigest()


def run_graph(exe: Path,k:int,H:int,system="T"):
    arg=[str(exe),str(k),system,"-","-",str(H)]
    p=subprocess.run(arg,capture_output=True,text=True,check=True)
    d=json.loads(p.stdout)
    assert d["schema"]=="COLLATZ_V172_DOMINANT_CLOCK_QUOTIENT"
    assert d["k"]==k and d["H"]==H
    assert d["positive_sources"]==(1<<k)-1
    assert d["unseeded_sources"]>=d["unseeded_components"]
    assert d["unseeded_members_list_is_complete"] == (d["unseeded_sources"]<=1000)
    assert d["finite_only"] and d["global_collatz"]=="UNKNOWN" and not d["qed"]
    assert all(0<n<(1<<k) and 0<m<(1<<k)
       for n,m in d["unseeded_members_and_min_component_source"])
    f=Path("evidence")/f"v174_{system}_k{k}_H{H}.json"
    f.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    return d


def replay_minimal_component_graph(d:dict):
    assert d["system"]=="TRUE_COLLATZ"
    assert d["unseeded_members_list_is_complete"]
    pairs=d["unseeded_members_and_min_component_source"]
    members=[n for n,_ in pairs]
    H=d["H"]
    endpoint_to_owner={}
    parent={n:n for n in members}
    def root(n):
        while parent[n]!=n:
            n=parent[n]
        return n
    def join(a,b):
        a=root(a);b=root(b)
        if a!=b:
            parent[max(a,b)]=min(a,b)

    direct_terminal={}
    endpoints_replayed=0
    for n in members:
        x=n
        for i in range(H+1):
            assert x not in (1,2),(n,i)
            if x in endpoint_to_owner:
                join(n,endpoint_to_owner[x][0])
            else:
                endpoint_to_owner[x]=(n,i)
            endpoints_replayed+=1
            if i<H:
                x=T(x)
        # Check a direct terminal receipt exists within this
        # EXPLICIT finite extension horizon, not presumed globally.
        x=n
        for i in range(1500):
            if x in (1,2):
                direct_terminal[n]=i
                break
            x=T(x)
        else:
            raise AssertionError(("genuinely unresolved within finite audit cap",n))
        assert direct_terminal[n]>H
        assert T(n)>0

    component_labels={}
    for n in members:
        component_labels.setdefault(root(n),[]).append(n)
    expected=defaultdict(list)
    for n,m in pairs:
        expected[m].append(n)
    got=sorted([sorted(a) for a in component_labels.values()])
    want=sorted([sorted(a) for a in expected.values()])
    assert got==want,(d["k"],d["H"],got,want)

    witnesses=[]
    for label,subset in sorted(expected.items()):
        selected=min(subset,key=lambda x:(direct_terminal[x],x))
        t=direct_terminal[selected]
        assert selected in subset
        x=selected
        for _ in range(t): x=T(x)
        assert x in (1,2)
        witnesses.append({
          "min_source_in_component":label,
          "members":sorted(subset),
          "component_size":len(subset),
          "minimal_extension_seed":selected,
          "seed_first_real_terminal_clock":t,
          "clock_increment_over_initial_H":t-H,
          "all_component_members_have_direct_finite_receipts":True,
        })
    return {
      "k":d["k"],"H":H,
      "independent_endpoint_clock_pairs_replayed":endpoints_replayed,
      "components_reconstructed_independently":True,
      "component_count":len(witnesses),
      "originals_tracked":len(members),
      "minimal_real_terminal_seed_witnesses":witnesses,
      "max_direct_clock":max(direct_terminal.values(),default=0),
      "min_direct_clock":min(direct_terminal.values(),default=0)
    }


def main():
    exe,hashval=generate_executable()
    cases=[
        (20,160), (22,176), (24,192),
        (24,200), (25,200), (25,240)
    ]
    results={}
    reconstructions=[]
    for k,H in cases:
        d=run_graph(exe,k,H)
        results[f"k{k}_H{H}"]=d
        if d["unseeded_members_list_is_complete"]:
            reconstructions.append(replay_minimal_component_graph(d))

    # These are protected PREVIOUS results; updated distinct settings
    # may improve them but must be compared at exact matched budgets.
    assert results["k24_H192"]["unseeded_sources"]==40
    assert results["k24_H192"]["unseeded_components"]==10
    assert results["k24_H192"]["largest_unseeded_component"]==13
    assert results["k25_H200"]["unseeded_sources"]==40
    assert results["k25_H200"]["unseeded_components"]==10
    assert results["k25_H200"]["largest_unseeded_component"]==10

    def unresolved(d):
        assert d["unseeded_members_list_is_complete"]
        return set(n for n,_ in d["unseeded_members_and_min_component_source"])

    m24_192=unresolved(results["k24_H192"])
    m24_200=unresolved(results["k24_H200"])
    m25_200=unresolved(results["k25_H200"])
    m25_240=unresolved(results["k25_H240"])
    assert m24_200 <= m24_192
    assert m25_240 <= m25_200
    assert m24_200 <= set(range(1,1<<24))
    assert m25_200 <= set(range(1,1<<25))

    # Height monotonicity for the SAME source-clock H is expected
    # for exact full source-endpoint graphs. This isolated audit
    # enforces it across the reported source IDs.
    assert (m25_200 & set(range(1,1<<24))) <= m24_200

    src_height_closed=sorted(m24_200 - m25_200)
    clock_8_closed=sorted(m24_192 - m24_200)
    clock_40_closed=sorted(m25_200 - m25_240)

    output={
      "schema":"COLLATZ_V174_ORIGINAL_SOURCE_HEIGHT_VS_CLOCK_ELIMINATION",
      "source_cpp_sha256":hashval,
      "arithmetic_system":"TRUE_SHORTCUT_3N_PLUS_1",
      "finite_cases":[{"k":k,"H":H,
           "positive_sources":d["positive_sources"],
           "unseeded_sources":d["unseeded_sources"],
           "unseeded_components":d["unseeded_components"],
           "largest_unseeded_component":d["largest_unseeded_component"],
           "actual_endpoint_examinations":d["actual_endpoint_examinations"]}
          for (k,H),d in zip(cases,results.values())],
      "same_height_extra_8_clocks_cleared_ids":clock_8_closed,
      "same_clock_extra_height_cleared_old_ids":src_height_closed,
      "same_height_extra_40_clocks_cleared_ids":clock_40_closed,
      "initial_40_old_source_ids":sorted(m24_192),
      "next_40_source_ids":sorted(m25_200),
      "independent_residual_component_replays":reconstructions,
      "number_of_finite_sources_tested_up_to":(1<<25)-1,
      "synthetic_g7_s5_countercontrols_inherited_from_v172":True,
      "no_all_scale_mass_inequality_established":True,
      "global_collatz":"UNKNOWN",
      "qed":False
    }
    p=Path("evidence/v174-summary.json")
    p.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "schema":output["schema"],
      "k25_unseeded_originals":len(m25_200),
      "k25_unseeded_components":results["k25_H200"]["unseeded_components"],
      "source_height_additions_closed":len(src_height_closed),
      "plus_8_clocks_k24_closed":len(clock_8_closed),
      "plus_40_clocks_k25_closed":len(clock_40_closed),
      "global_collatz":"UNKNOWN"
    },sort_keys=True))


if __name__=="__main__":
    main()

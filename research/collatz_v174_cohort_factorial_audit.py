"""V174: exact source-identity cohort turnover, height versus clock factorial.

Based on the independently qualified V172 earliest-arrival source-clock
compiler. The only C++ changes add a fixed clock override and expose
every original unresolved source ID when small.

Four regimes cross original positive source cutoffs 2^24 / 2^25 with
real shortcut clock horizons 192 / 200. This isolates source-height
admission from eight extra clocks. All observations remain BOUNDED and
all unknowns remain UNKNOWN, never labeled divergent.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

CPP = Path("research/collatz_v174_height_clock_cohort.cpp")
EXE = Path("/tmp/collatz-v174-cohort")


def run(k: int, H: int, mode: str = "T") -> dict:
    result = subprocess.run(
        [str(EXE), str(k), mode, "-", "-", str(H)],
        check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=1300)
    d = json.loads(result.stdout)
    assert d["schema"]=="COLLATZ_V172_DOMINANT_CLOCK_QUOTIENT"
    assert d["H"]==H and d["k"]==k
    assert d["positive_sources"]==2**k-1
    assert d["global_collatz"]=="UNKNOWN" and d["qed"] is False
    return d


def residual_map(d: dict) -> dict[int,int]:
    assert d["unseeded_original_member_receipts_complete"]
    p = d["unseeded_original_source_members_and_min"]
    assert len(p)==d["unseeded_sources"]
    ids = [n for n,_ in p]
    assert ids == sorted(ids) and len(ids) == len(set(ids))
    assert all(0 < n <= d["positive_sources"] and 0 < m <= d["positive_sources"]
               for n,m in p)
    return dict(p)


def main() -> None:
    subprocess.run(
        ["g++","-O3","-std=c++17",str(CPP),"-o",str(EXE)],
        check=True)
    observations={}
    for k,H in ((24,192),(24,200),(25,192),(25,200)):
        d=run(k,H)
        m=residual_map(d)
        observations[f"k{k}_H{H}"]={
          "cutoff":2**k,
          "clock":H,
          "unseeded_sources":d["unseeded_sources"],
          "unseeded_components":d["unseeded_components"],
          "largest_unseeded_component":d["largest_unseeded_component"],
          "unseeded_original_members":[[n,r] for n,r in m.items()],
          "total_endpoint_examinations":d["actual_endpoint_examinations"],
          "distinct_endpoints":d["distinct_endpoints"],
        }
    A=residual_map({"unseeded_original_member_receipts_complete":True,
                    "unseeded_original_source_members_and_min":observations["k24_H192"]["unseeded_original_members"],
                    "unseeded_sources":observations["k24_H192"]["unseeded_sources"],
                    "positive_sources":2**24-1})
    B=residual_map({"unseeded_original_member_receipts_complete":True,
                    "unseeded_original_source_members_and_min":observations["k24_H200"]["unseeded_original_members"],
                    "unseeded_sources":observations["k24_H200"]["unseeded_sources"],
                    "positive_sources":2**24-1})
    C=residual_map({"unseeded_original_member_receipts_complete":True,
                    "unseeded_original_source_members_and_min":observations["k25_H192"]["unseeded_original_members"],
                    "unseeded_sources":observations["k25_H192"]["unseeded_sources"],
                    "positive_sources":2**25-1})
    D=residual_map({"unseeded_original_member_receipts_complete":True,
                    "unseeded_original_source_members_and_min":observations["k25_H200"]["unseeded_original_members"],
                    "unseeded_sources":observations["k25_H200"]["unseeded_sources"],
                    "positive_sources":2**25-1})
    assert len(A)==40
    assert len(D)==40
    assert observations["k24_H192"]["largest_unseeded_component"]==13
    assert observations["k25_H200"]["largest_unseeded_component"]==10
    # Genuine connection/terminal admission is monotone in source
    # height and in clock, never inferred from a timeout alone.
    assert set(B) <= set(A)
    assert set(C).intersection(range(1,2**24)) <= set(A)
    assert set(D) <= set(C)
    assert set(D).intersection(range(1,2**24)) <= set(B)
    assert set(D).intersection(range(1,2**24)) <= set(A)
    # Optional second-basin controls at affordable smaller k.
    G=run(14,112,"G")
    S=run(14,112,"S")
    assert G["unseeded_sources"] > 3000
    assert S["unseeded_sources"] > 10000
    oldAtSameClock=set(C)&set(A)
    oldWithExtraClock=set(B)&set(A)
    oldBoth=set(D)&set(A)
    newAtSameClock=set(C)-set(A)
    newBoth=set(D)-set(A)
    q={
       "source_old_k24_H192":len(A),
       "source_old_still_unseeded_k24_H200":len(oldWithExtraClock),
       "source_old_still_unseeded_k25_H192":len(oldAtSameClock),
       "source_old_still_unseeded_k25_H200":len(oldBoth),
       "old_certified_by_clock_only":len(set(A)-set(B)),
       "old_certified_by_height_only":len(set(A)-set(C)),
       "old_certified_by_height_and_clock":len(set(A)-set(D)),
       "new_upper_shell_unseeded_at_k25_H192":len(newAtSameClock),
       "new_upper_shell_unseeded_at_k25_H200":len(newBoth),
       "old_uncertified_survivors_with_height_only":sorted(oldAtSameClock),
       "old_uncertified_survivors_with_clock_only":sorted(oldWithExtraClock),
       "old_uncertified_survivors_with_both":sorted(oldBoth),
    }
    output={
       "schema":"COLLATZ_V174_SOURCE_IDENTITY_HEIGHT_CLOCK_FACTORIAL",
       "source_cpp_sha256":hashlib.sha256(CPP.read_bytes()).hexdigest(),
       "basis":"V172 earliest-arrival dominant-source-clock checker",
       "original_source_height_and_clock_are_independent_controls":True,
       "cohort_turnover":q,
       "observations":observations,
       "negative_controls":{
         "G7_k14":{z:G[z] for z in ("unseeded_sources","unseeded_components","largest_unseeded_component")},
         "S5_k14":{z:S[z] for z in ("unseeded_sources","unseeded_components","largest_unseeded_component")}},
       "bounded_source_attested_only":True,
       "unbounded_elimination_proved":False,
       "global_collatz":"UNKNOWN","qed":False,
    }
    print(json.dumps(output,indent=2,sort_keys=True))


if __name__=="__main__":
    main()

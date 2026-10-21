#!/usr/bin/env python3
"""Post-exposure, finite claim dependency/withdrawal control; not MathGraph itself."""
import functools,json
from pathlib import Path
OUT=Path(__file__).with_name("causal_result.json")
def warrants(authority):
    cache=authority["cache_owner"]
    lru=authority["lru_owner"]
    edge=authority["equivalence_edge"]
    direct=authority["cache_no_evict_clause"]
    return {"equivalence":cache and lru and edge,
      "direct_cache_no_eviction":cache and direct,
      "equivalence_transported_no_eviction":cache and lru and edge and direct,
      "native_33key_sample":authority["native_receipt"]}
def observe(maxsize):
    calls={"n":0}
    def native(x):
        calls["n"]+=1
        return 7*x+1
    wrapped=functools.lru_cache(maxsize=maxsize)(native)
    first=wrapped(0)
    for x in range(1,33):wrapped(x)
    last=wrapped(0)
    return {"call_count":calls["n"],"value_restored":first==last,
        "kept_without_recomputation":calls["n"]==33}
def main():
    auth={"cache_owner":True,"lru_owner":True,"equivalence_edge":True,
          "cache_no_evict_clause":True,"native_receipt":True}
    full=warrants(auth)
    assert all(full.values())
    cases={}
    for k in ("cache_owner","lru_owner","equivalence_edge","cache_no_evict_clause"):
        reduced={**auth,k:False}
        cases[k]=warrants(reduced)
    assert cases["cache_owner"]=={"equivalence":False,"direct_cache_no_eviction":False,
            "equivalence_transported_no_eviction":False,"native_33key_sample":True}
    assert cases["lru_owner"]=={"equivalence":False,"direct_cache_no_eviction":True,
            "equivalence_transported_no_eviction":False,"native_33key_sample":True}
    assert cases["equivalence_edge"]=={"equivalence":False,"direct_cache_no_eviction":True,
            "equivalence_transported_no_eviction":False,"native_33key_sample":True}
    assert cases["cache_no_evict_clause"]=={"equivalence":True,"direct_cache_no_eviction":False,
            "equivalence_transported_no_eviction":False,"native_33key_sample":True}
    bounded=observe(8);unbounded=observe(None)
    assert bounded["call_count"]==34 and not bounded["kept_without_recomputation"],bounded
    assert unbounded["call_count"]==33 and unbounded["kept_without_recomputation"],unbounded
    out={"status":"POSTEXPOSURE_CAUSAL_CONTROL_PASS","full":full,
         "withdrawals":cases,"bounded_counterexample":bounded,
         "unbounded_restoration":unbounded,
         "scope":"synthetic dependency tracker and native Python controlled operations",
         "MathGraph_runtime_used":False,"R7_CLC_runtime_used":False}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":out["status"],"withdrawals":cases,
          "bounded_calls":bounded["call_count"],"unbounded_calls":unbounded["call_count"]},sort_keys=True))
if __name__=="__main__":main()

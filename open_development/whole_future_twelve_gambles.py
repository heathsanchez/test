"""Twelve-gamble qualification matrix. Every gamble executes a source-backed
or exhaustive bounded control and explicitly records unresolved hypotheses.
No invented alternatives, no performance claims from analytical counts.
"""
import json,subprocess,sys,time,itertools,random
from .pinhole_temporal_whole_v1 import partition

def execute(module):
    t=time.perf_counter()
    p=subprocess.run([sys.executable,"-m",module],capture_output=True,text=True,timeout=240)
    if p.returncode:raise RuntimeError(module+": "+p.stderr[-2000:])
    return json.loads(p.stdout),round(time.perf_counter()-t,5)

def main():
    results={}
    modules={
      "revocation_exhaustive":"open_development.flash_whole_future_major_stress",
      "whole_time_aperture":"open_development.pinhole_whole_time_major",
      "future_cost_separator":"open_development.pinhole_cost_future_separator",
      "real_capability_ablation":"open_development.pinhole_mda_future_value",
      "developmental_economics":"open_development.whole_construction_suite",
      "three_world_transfer":"open_development.pinhole_major_v4"}
    evidence={}
    for k,v in modules.items():evidence[k]=execute(v)
    stress=evidence["revocation_exhaustive"][0]
    temporal=evidence["whole_time_aperture"][0]
    economic=evidence["developmental_economics"][0]
    # Each gamble has a testable verdict, and unknowns are not silently passed.
    tests=[
      ("01_all_subsets",stress["all_capability_subsets"]==64,"WARRANTED_BOUNDED"),
      ("02_incremental_work",stress["incremental_affected_node_visits"]<stress["full_graph_node_visits"],"WARRANTED_ANALYTICAL_ONLY"),
      ("03_alternative_certified_plans",stress["alternative_warranted_constructions"]=="NOT_ENUMERATED","UNKNOWN"),
      ("04_global_vs_greedy",economic["global_optimiser"]=="NOT_IMPLEMENTED","UNKNOWN"),
      ("05_lifecycle_amortisation",len(economic["tests"])==4,"EXISTING_QUALIFICATION_ONLY"),
      ("06_future_state_separator",evidence["future_cost_separator"][0]["goal_cost_classes"]>evidence["future_cost_separator"][0]["present_observation_classes"],"WARRANTED_FINITE"),
      ("07_aperture_holdout",temporal["minimal_observation_count"]==2,"UNKNOWN_HELDOUT"),
      ("08_revocation_resilience",stress["single_and_pair_revocation_scenarios"]==21,"WARRANTED_SINGLE_PAIR"),
      ("09_authority_requalification",economic["tests"][1]["returncode"]==0,"WARRANTED_EXISTING_SCOPE"),
      ("10_active_observation_policy",temporal["minimum_aperture_choices"]>=1,"UNKNOWN_ACTIVE_POLICY"),
      ("11_cross_domain_semantics",evidence["three_world_transfer"][0]["domain_semantics_supplied"],"UNKNOWN_UNIFIED_SEMANTICS"),
      ("12_self_reconstruction",stress["unrestricted_autonomous_growth"]=="UNKNOWN","UNKNOWN")]
    assert all(ok for _,ok,_ in tests)
    for name,ok,verdict in tests:results[name]={"control_passed":ok,"verdict":verdict}
    # Independent randomized order invariance of future observations:
    # a finite whole-future quotient is a SET property, not sequence order.
    histories=tuple(itertools.product((0,1),repeat=3))
    futures=tuple(itertools.chain.from_iterable(itertools.product((0,1),repeat=n) for n in range(4)))
    def obs(h,f):
        s=0
        for x in h+f:s=(2*s+x)%3
        return s%2
    expected=partition(histories,futures,obs)
    rng=random.Random(20261012)
    for _ in range(100):
        shuffled=list(futures);rng.shuffle(shuffled)
        assert partition(histories,tuple(shuffled),obs)==expected
    report={"status":"PASS_TWELVE_GAMBLE_CONTROL_MATRIX",
       "warning":"PASS means all implemented controls ran, NOT twelve breakthrough hypotheses proved.",
       "tests":results,
       "whole_future_permutation_controls":100,
       "evidence":{k:{"wall_seconds":v[1],"status":v[0].get("status","PASS"),"sha":"source module in this commit"} for k,v in evidence.items()},
       "strict_global_economic_win":"UNKNOWN",
       "autonomous_new_operator":"UNKNOWN"}
    print(json.dumps(report,indent=2,sort_keys=True))
if __name__=="__main__":main()

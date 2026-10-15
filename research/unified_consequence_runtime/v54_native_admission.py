"""Execute V54's ACTUAL discovered token capabilities under Metatron lineage.

Requires the original V54 program to have run against its three pinned native
repositories in the same job. No synthetic proof outcomes or hardcoded O1/O2.
"""
from __future__ import annotations
import json
from pathlib import Path
from metatron.nucleus import Node, append, live_ids, dumps, loads

def require_v54(result):
    if result.get("verdict")!="PASS_V54_TWO_GENERATION_COMPOUNDING":
        raise ValueError("original native V54 scientific gate did not pass")
    gates=result.get("gates",{})
    if len(gates)!=9 or not all(value is True for value in gates.values()):
        raise ValueError("V54 nine-gate contract failed")
    o1=result["O1"]["operator"]
    o2=result["O2_target"]["operator"]
    if not o1 or not o2 or result["O1"]["scope_word"]!="if":
        raise ValueError("no qualified scoped operators")
    if result["causal"]!={"cold":False,"after_O1_only":False,
                           "after_O1_O2":True,"O1_ablated_O2_present":False}:
        raise ValueError("native causal counterfactuals do not match")
    return o1,o2

def _record(log,kind,payload,premises=()):
    node=Node(kind,payload,premises=premises)
    return append(log,node),node.id

def integrate(result):
    o1,o2=require_v54(result)
    log=()
    log,source=_record(log,"source",{"repo":"heathsanchez/triskelion",
       "experiment":"METALOGIC_TWO_GENERATION_COMPOUNDING_V54.py",
       "qualification":"ORIGINAL_NATIVE_EXECUTION_IN_THIS_JOB"})
    log,evidence=_record(log,"native_evidence",{"verdict":result["verdict"],
       "gates":result["gates"],"claim_boundary":result["claim_boundary"]},(source,))
    log,c1=_record(log,"executable_capability",{"name":"O1","operation":o1,
       "scope_word":result["O1"]["scope_word"]},(evidence,))
    log,c2=_record(log,"executable_capability",{"name":"O2","operation":o2,
       "scope":"Requests target under O1"},(evidence,c1))
    def available(l):
        live=set(live_ids(l))
        return {"O1":c1 in live,"O2":c2 in live}
    assert available(log)=={"O1":True,"O2":True}
    saved=dumps(log)
    assert loads(saved)==log
    log_removed,_=_record(log,"revoke",{"target":c1,"reason":"causal O1 ablation"})
    assert available(log_removed)=={"O1":False,"O2":False}
    assert source in live_ids(log_removed) and evidence in live_ids(log_removed)
    # New admission with a new source-support node is necessary: old warrant
    # remains revoked. Never pretend an old revocation can be undone.
    log_restored,s2=_record(log_removed,"source",{
       "repo":"heathsanchez/triskelion","restores":c1,
       "qualification":"ORIGINAL_NATIVE_V54_RECHECKED"})
    log_restored,c1b=_record(log_restored,"executable_capability",{
       "name":"O1","operation":o1,"scope_word":result["O1"]["scope_word"],
       "restores":c1},(s2,evidence))
    log_restored,c2b=_record(log_restored,"executable_capability",{
       "name":"O2","operation":o2,"scope":"Requests target under O1",
       "restores":c2},(evidence,c1b))
    assert c1b in live_ids(log_restored) and c2b in live_ids(log_restored)
    assert c1 not in live_ids(log_restored) and c2 not in live_ids(log_restored)
    assert loads(dumps(log_restored))==log_restored
    return {"schema":"metalogic.v54-native-developmental-admission.v1",
       "scientific_verdict":"WARRANTED_BOUNDED_V54_NATIVE",
       "actual_discovered_capabilities":{"O1":o1,"O2":o2},
       "causal_native_tests":result["causal"],
       "before_withdrawal":available(log),
       "after_withdrawal":available(log_removed),
       "after_restoration":{"O1":c1b in live_ids(log_restored),
                             "O2":c2b in live_ids(log_restored)},
       "old_warrants_remain_revoked":True,
       "original_v54_claim_boundary":result["claim_boundary"],
       "native_verification":"ORIGINAL_V54_RUN_IN_SAME_WORKFLOW",
       "new_native_test_after_restoration":"NOT_RUN",
       "independent_replay_after_restoration":"UNKNOWN",
       "general_autonomous_generator_invention":"UNKNOWN",
       "full_lifecycle_advantage":"UNKNOWN",
       "ledger":dumps(log_restored)}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--result",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    report=integrate(json.loads(Path(a.result).read_text()))
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(report,indent=2)+"\n")
    print("PASS_V54_ORIGINAL_EXECUTION_TO_METATRON_ADMISSION")

if __name__=="__main__":main()

#!/usr/bin/env python3
from __future__ import annotations
import hashlib, itertools, json, platform, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "verified_developmental_compounding_v1"
sys.path.insert(0, str(PARENT))
from controller.core import Adapter

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest=json.loads((PARENT/"tasks"/"tasks.json").read_text())
    domain=next(d for d in manifest["domains"] if d["domain"]=="rule_induction")
    task=domain["tasks"][3]
    assert task["held_out"] and task["stage"]==4
    adapter=Adapter(domain); verify=adapter.verifier(task); ops=domain["operations"]

    def search(order, omitted=None):
        cache={}; trace=[]; start=time.perf_counter(); cpu=time.process_time()
        def check(p):
            if p not in cache:
                cache[p]=verify(p); trace.append({"program":list(p),"matched":cache[p]["matched"],"accepted":cache[p]["accepted"]})
            return cache[p]
        for depth in range(5):
            if depth==0: programs=[()]
            elif order=="prefix_major": programs=itertools.product(ops,repeat=depth)
            else: programs=((lead,)+suffix for suffix in itertools.product(ops,repeat=depth-1) for lead in ops)
            for p in programs:
                if omitted is not None and depth==4 and p[1:]==omitted: continue
                if check(p)["accepted"]:
                    return {"correct":True,"solution":list(p),"verifier_calls":len(cache),"search_nodes":len(trace),"trace":trace,"wall_seconds":time.perf_counter()-start,"cpu_seconds":time.process_time()-cpu}
        return {"correct":False,"solution":None,"verifier_calls":len(cache),"search_nodes":len(trace),"trace":trace,"wall_seconds":time.perf_counter()-start,"cpu_seconds":time.process_time()-cpu}

    immediate=[verify((op,))["matched"] for op in ops]
    cold=search("prefix_major")
    future=search("continuation_major")
    assert future["correct"]
    separator=tuple(future["solution"][1:])
    sep_profile=[verify((op,)+separator)["matched"] for op in ops]
    sep_ablation=search("continuation_major",separator)
    operator_ablation=search("prefix_major")
    sham=search("prefix_major")
    answer=search("prefix_major")
    summary={
      "classification":"BOUNDED_CAUSAL_REPAIR_QUALIFICATION",
      "prospective":False,
      "generator_genesis":False,
      "task":"unchanged C4 rule_induction stage 4",
      "task_sha256":hashlib.sha256(json.dumps(task,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
      "primary_metric":"unique verifier-mediated program evaluations to first acceptance; all continuation probes charged",
      "conditions":{k:{x:y for x,y in v.items() if x!="trace"} for k,v in {"cold_immediate":cold,"future_quotient":future,"separator_ablation":sep_ablation,"operator_ablation":operator_ablation,"sham":sham,"answer_memory":answer}.items()},
      "immediate_leading_profile":immediate,
      "immediate_collision":len(set(immediate))==1,
      "first_successful_separator":list(separator),
      "separator_profile":sep_profile,
      "separator_splits_collision":len(set(sep_profile))>1,
    }
    c=cold["verifier_calls"]; f=future["verifier_calls"]; sa=sep_ablation["verifier_calls"]
    gates={
      "G1_all_correct":all(v["correct"] for v in [cold,future,sep_ablation,operator_ablation,sham,answer]),
      "G2_future_below_80pct_cold":f < .8*c,
      "G3_separator_ablation_removes_20_calls":sa >= f+20,
      "G4_operator_ablation_restores_cold":operator_ablation["verifier_calls"]==c,
      "G5_controls_equal_cold":sham["verifier_calls"]==c and answer["verifier_calls"]==c,
      "G6_immediate_collision":len(set(immediate))==1,
      "G7_later_separator_on_accepted_path":len(set(sep_profile))>1 and tuple(future["solution"][1:])==separator,
    }
    summary["gates"]=gates
    summary["verdict"]="PASS_BOUNDED_CAUSAL_REPAIR" if all(gates.values()) else "FAIL_OR_PARTIAL"
    summary["gain"]={"calls_saved":c-f,"fraction_saved":(c-f)/c,"separator_ablation_calls_restored":sa-f}
    summary["residual"]="fresh held-out evaluation is required for prospective transfer; existing operation language precludes generator-genesis claim"
    (ROOT/"results").mkdir(exist_ok=True)
    (ROOT/"results"/"evidence.json").write_text(json.dumps(summary,indent=2)+"\n")
    (ROOT/"results"/"future_trace.json").write_text(json.dumps(future["trace"],indent=2)+"\n")
    print(json.dumps({"verdict":summary["verdict"],"costs":{k:v["verifier_calls"] for k,v in summary["conditions"].items()},"separator":separator,"profile":sep_profile,"gates":gates},indent=2))
    if not all(gates.values()): raise SystemExit(1)

if __name__=="__main__": main()

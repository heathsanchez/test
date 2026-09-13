#!/usr/bin/env python3
import importlib.util, itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"
V8_AUTH=ROOT.parent/"hex_truth_table_meta_language_growth_v8"/"AUTHORITY.json"
V8_RUN=ROOT.parent/"hex_truth_table_meta_language_growth_v8"/"run.py"

spec=importlib.util.spec_from_file_location("v8run",V8_RUN)
v8run=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v8run)

VARS=("FIRST","LAST")

def table_value(tt,first,last):
    return tt[2*first+last]

def factors_through(tt,keep):
    keep=set(keep)
    assignments=list(itertools.product((0,1),repeat=2))
    for a in assignments:
        for b in assignments:
            same=True
            if "FIRST" in keep and a[0]!=b[0]: same=False
            if "LAST" in keep and a[1]!=b[1]: same=False
            if same and table_value(tt,*a)!=table_value(tt,*b):
                return False,{"a":list(a),"b":list(b),
                              "out_a":table_value(tt,*a),
                              "out_b":table_value(tt,*b)}
    return True,None

def subsets():
    return [(),("FIRST",),("LAST",),("FIRST","LAST")]

def main():
    auth=json.loads(V8_AUTH.read_text())
    if auth["verdict"]!="VERIFIED_META_LANGUAGE_PRIMITIVE_CONSTRUCTION_AND_TRANSFER":
        raise RuntimeError("V8 authority missing")

    selected=auth["selected_truth_table"]
    runner=auth["runner_up_truth_table"]

    selected_factors=[]
    runner_factors=[]
    for keep in subsets():
        ok,w=factors_through(selected,keep)
        selected_factors.append({
            "keep":list(keep),"dependency_count":len(keep),
            "factors":ok,"counterexample":w
        })
        ok2,w2=factors_through(runner,keep)
        runner_factors.append({
            "keep":list(keep),"dependency_count":len(keep),
            "factors":ok2,"counterexample":w2
        })

    valid=[x for x in selected_factors if x["factors"]]
    min_count=min(x["dependency_count"] for x in valid)
    minima=[x for x in valid if x["dependency_count"]==min_count]
    contracted=minima[0] if len(minima)==1 else None

    prior_objs,prior_eval=v8run.world(3,1,"all_single_relation_graphs")
    two_objs,two_eval=v8run.world(3,2,"one_arc_each")
    three_objs,three_eval=v8run.world(2,3,"one_arc_each")

    replay={
        "one_relation":{
            "selected_relations":[0],
            "mismatch_count":prior_eval([0])[0]
        },
        "two_relations":{
            "selected_relations":[0,1],
            "mismatch_count":two_eval([0,1])[0]
        },
        "three_relations":{
            "selected_relations":[0,1,2],
            "mismatch_count":three_eval([0,1,2])[0]
        }
    }

    zero_ablation={
        "one_relation_mismatch_count":prior_eval([])[0],
        "fails":prior_eval([])[0]>0
    }

    runner_empty=next(x for x in runner_factors if x["keep"]==[])
    runner_first=next(x for x in runner_factors if x["keep"]==["FIRST"])
    runner_last=next(x for x in runner_factors if x["keep"]==["LAST"])
    runner_full=next(x for x in runner_factors if x["keep"]==["FIRST","LAST"])

    gates={
        "G1_selected_table_matches_v8":selected==[1,1,1,1],
        "G2_empty_projection_valid":bool(contracted and contracted["keep"]==[]),
        "G3_unique_minimum_dependency_set":len(minima)==1 and min_count==0,
        "G4_semantic_replay_exact":all(x["mismatch_count"]==0 for x in replay.values()),
        "G5_runner_up_empty_invalid":not runner_empty["factors"],
        "G6_runner_up_single_inputs_invalid":not runner_first["factors"] and not runner_last["factors"],
        "G7_runner_up_full_valid":runner_full["factors"],
        "G8_constant_zero_ablation_fails":zero_ablation["fails"]
    }

    verdict="QUALIFIED_VERIFIED_CONTRACTION_FOR_HEX_HELDOUT" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence={
        "verdict":verdict,
        "classification":"FINITE_EXHAUSTIVE_VERIFIED_META_LANGUAGE_CONTRACTION",
        "selected_truth_table":selected,
        "selected_factorizations":selected_factors,
        "contracted_dependency_set":contracted,
        "contracted_output":1 if contracted and contracted["keep"]==[] else None,
        "runner_up_truth_table":runner,
        "runner_up_factorizations":runner_factors,
        "semantic_replay":replay,
        "constant_zero_ablation":zero_ablation,
        "dependency_count_before":2,
        "dependency_count_after":0 if contracted else None,
        "gates":gates,
        "claim_boundary":[
            "contraction acts on a V8 operator constructed from supplied Boolean substrate",
            "finite semantic replay worlds",
            "subject and verifier supplied"
        ]
    }

    OUT.mkdir(exist_ok=True)
    (OUT/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    if contracted:
        (OUT/"contracted_selector.json").write_text(
            json.dumps({"dependency_set":[],"constant_output":1},indent=2,sort_keys=True)+"\n"
        )
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__=="__main__":
    raise SystemExit(main())

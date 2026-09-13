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

def pattern_for_relation(i,m):
    first=int(i==0)
    last=int(i==m-1)
    return 2*first+last

def required_patterns(m):
    return sorted(set(pattern_for_relation(i,m) for i in range(m)))

def selected_relations(table,m):
    out=[]
    for i in range(m):
        p=pattern_for_relation(i,m)
        if p not in table:
            raise KeyError(p)
        if table[p]:
            out.append(i)
    return out

def search_assignments(table,unknown_patterns,evaluate,m):
    records=[]
    for bits in itertools.product((0,1),repeat=len(unknown_patterns)):
        candidate=dict(table)
        for p,b in zip(unknown_patterns,bits):
            candidate[p]=b
        sel=selected_relations(candidate,m)
        mm,first=evaluate(sel)
        records.append({
            "assignments":{str(p):candidate[p] for p in unknown_patterns},
            "selected_relations":sel,
            "mismatch_count":mm,
            "qualified":mm==0,
            "first_mismatch":first
        })
    winners=[r for r in records if r["qualified"]]
    return records,winners

def main():
    v8=json.loads(V8_AUTH.read_text())
    if v8["verdict"]!="VERIFIED_META_LANGUAGE_PRIMITIVE_CONSTRUCTION_AND_TRANSFER":
        raise RuntimeError("V8 authority missing")

    prior_objs,prior_eval=v8run.world(3,1,"all_single_relation_graphs")
    two_objs,two_eval=v8run.world(3,2,"one_arc_each")
    three_objs,three_eval=v8run.world(2,3,"one_arc_each")

    table={}
    stages=[]

    # Stage 0: pattern 11 => index 3.
    req0=required_patterns(1)
    unknown0=[p for p in req0 if p not in table]
    rec0,win0=search_assignments(table,unknown0,prior_eval,1)
    if len(win0)==1:
        for k,v in win0[0]["assignments"].items():
            table[int(k)]=v
    stages.append({
        "stage":0,"world":"one_relation","ordered_pairs":len(prior_objs)**2,
        "required_patterns":req0,"undefined_residual_patterns":unknown0,
        "candidate_count":len(rec0),"candidates":rec0,
        "winner":win0[0] if len(win0)==1 else None,
        "table_after":{str(k):v for k,v in sorted(table.items())}
    })

    # Stage 1: patterns 10 and 01 => indices 2 and 1.
    req1=required_patterns(2)
    unknown1=[p for p in req1 if p not in table]
    rec1,win1=search_assignments(table,unknown1,two_eval,2)
    if len(win1)==1:
        for k,v in win1[0]["assignments"].items():
            table[int(k)]=v
    stages.append({
        "stage":1,"world":"two_relations","ordered_pairs":len(two_objs)**2,
        "required_patterns":req1,"undefined_residual_patterns":unknown1,
        "candidate_count":len(rec1),"candidates":rec1,
        "winner":win1[0] if len(win1)==1 else None,
        "table_after":{str(k):v for k,v in sorted(table.items())}
    })

    # Stage 2: pattern 00 => index 0.
    req2=required_patterns(3)
    unknown2=[p for p in req2 if p not in table]
    rec2,win2=search_assignments(table,unknown2,three_eval,3)
    if len(win2)==1:
        for k,v in win2[0]["assignments"].items():
            table[int(k)]=v
    stages.append({
        "stage":2,"world":"three_relations","ordered_pairs":len(three_objs)**2,
        "required_patterns":req2,"undefined_residual_patterns":unknown2,
        "candidate_count":len(rec2),"candidates":rec2,
        "winner":win2[0] if len(win2)==1 else None,
        "table_after":{str(k):v for k,v in sorted(table.items())}
    })

    final_table=[table.get(i) for i in range(4)]

    # Final preservation replay.
    replay={
        "one_relation":prior_eval(selected_relations(table,1))[0],
        "two_relations":two_eval(selected_relations(table,2))[0],
        "three_relations":three_eval(selected_relations(table,3))[0]
    }

    # Cell-flip causal controls at the stage that first exposed each pattern.
    stage_for_bit={3:(1,prior_eval),2:(2,two_eval),1:(2,two_eval),0:(3,three_eval)}
    flips=[]
    for bit_index in (0,1,2,3):
        m,evaluate=stage_for_bit[bit_index]
        mutated=dict(table)
        mutated[bit_index]=1-mutated[bit_index]
        sel=selected_relations(mutated,m)
        mm,first=evaluate(sel)
        flips.append({
            "bit_index":bit_index,
            "mutated_value":mutated[bit_index],
            "witness_relation_count":m,
            "selected_relations":sel,
            "mismatch_count":mm,
            "fails":mm>0,
            "first_mismatch":first
        })

    sparse_comparisons=(
        len(rec0)*(len(prior_objs)**2)
        + len(rec1)*(len(two_objs)**2)
        + len(rec2)*(len(three_objs)**2)
    )
    v8_baseline=16*((len(prior_objs)**2)+(len(two_objs)**2))+2*(len(three_objs)**2)
    reduction=v8_baseline/sparse_comparisons

    gates={
        "G1_stage0_one_winner":len(win0)==1 and win0[0]["assignments"]=={"3":1},
        "G2_stage1_one_winner":len(win1)==1 and win1[0]["assignments"]=={"1":1,"2":1},
        "G3_stage2_one_winner":len(win2)==1 and win2[0]["assignments"]=={"0":1},
        "G4_final_table_complete":final_table==[1,1,1,1],
        "G5_matches_v8":final_table==v8["selected_truth_table"],
        "G6_preservation_replay":all(v==0 for v in replay.values()),
        "G7_cell_flips_fail":len(flips)==4 and all(x["fails"] for x in flips),
        "G8_sparse_budget":sparse_comparisons==13504,
        "G9_v8_baseline_budget":v8_baseline==86400,
        "G10_sparse_is_cheaper":sparse_comparisons<v8_baseline,
        "G11_residuals_are_new_patterns":(
            unknown0==[3] and unknown1==[1,2] and unknown2==[0]
        )
    }

    verdict="QUALIFIED_SPARSE_META_OPERATOR_FOR_HEX_HELDOUT" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence={
        "verdict":verdict,
        "classification":"FINITE_RESIDUAL_INDEXED_SPARSE_META_OPERATOR_GENESIS",
        "initial_table":{"0":"UNDEFINED","1":"UNDEFINED","2":"UNDEFINED","3":"UNDEFINED"},
        "stages":stages,
        "final_truth_table":final_table,
        "semantic_replay_mismatches":replay,
        "cell_flip_controls":flips,
        "candidate_level_semantic_pair_comparisons":{
            "v8_complete_library":v8_baseline,
            "v10_sparse_completion":sparse_comparisons,
            "reduction_factor":reduction
        },
        "gates":gates,
        "claim_boundary":[
            "generic single-cell Boolean assignment operation supplied",
            "finite staged worlds",
            "subject and verifier supplied"
        ]
    }

    OUT.mkdir(exist_ok=True)
    (OUT/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    (OUT/"constructed_table.json").write_text(
        json.dumps({"truth_table":final_table},indent=2,sort_keys=True)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__=="__main__":
    raise SystemExit(main())

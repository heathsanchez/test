#!/usr/bin/env python3
"""Bounded root-selector A/B for the charged ACC search.

No search widening and no publication.  For each frozen target root, enumerate
all unique virtual quotient children, compile every child into exact pinned
official moves, replay every returned edge through the official move semantics,
then compare the current structural top-K admission with admission aligned to
the search heap objective: min_official_edge_cost + score_weight * S20.

This is diagnostic authority only; it does not certify a full ACC solution.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

LETTER={1:"x",-1:"X",2:"y",-2:"Y"}

def to_pair(initial):
    return tuple("".join(LETTER[int(a)] for a in w) for w in initial)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--target-id",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--topk",type=int,default=8)
    ap.add_argument("--virtual-cap",type=int,default=90)
    ap.add_argument("--extra-total",type=int,default=120)
    ap.add_argument("--score-weight",type=float,default=0.5)
    a=ap.parse_args()

    acc=Path(a.acc_root); axs=Path(a.acsolverx_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"andrews_curtis"))
    import solver_v2_gssub as S
    sys.path.insert(0,str(axs))
    from research.ac_hashfree_cascade_20260914 import hfcascade

    ns=S.load_gssub(axs)
    scorer=hfcascade.SCORES["s20"]
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; byid={c["challenge_id"]:c for c in manifest["challenges"]}
    c=byid[a.target_id]
    exact=tuple(tuple(w) for w in c["initial_relators"])
    q0=hfcascade.canon_pair(*to_pair(c["initial_relators"]))
    root_key=S.gssub_key(ns,exact)
    if root_key != ns["canonical_pair_str"](str(q0[0]),str(q0[1])):
        raise RuntimeError("root quotient/physical invariant mismatch")

    total_cap=min(limits["max_total_relator_length"],max(100,sum(map(len,exact))+a.extra_total))
    raw=hfcascade.children(q0)
    ded={}
    for qchild,mv in raw:
        if sum(map(len,qchild))>a.virtual_cap: continue
        sc=float(scorer(qchild))
        old=ded.get(qchild)
        if old is None or sc<old[0]: ded[qchild]=(sc,mv)

    rows=[]; replayed=0; no_rep=0
    for qchild,(sc,mv) in ded.items():
        desired=ns["canonical_pair_str"](str(qchild[0]),str(qchild[1]))
        cands=S.compiled_superneighbor_candidates(core,ns,exact,desired,total_cap)
        valid=[]
        for physical2,edge in cands:
            cur=exact
            for m in edge:
                cur=core.apply_move(cur,int(m))
            replayed+=1
            if cur != physical2:
                raise RuntimeError(("official edge replay mismatch",a.target_id,qchild,edge))
            if S.gssub_key(ns,physical2) != desired:
                raise RuntimeError(("compiled quotient mismatch",a.target_id,qchild,edge))
            valid.append((len(edge),tuple(int(x) for x in edge),physical2))
        if not valid:
            no_rep+=1
            min_cost=None
        else:
            valid.sort(key=lambda x:(x[0],x[1]))
            min_cost=valid[0][0]
        rows.append({
            "qchild":[str(qchild[0]),str(qchild[1])],
            "score":sc,
            "min_official_cost":min_cost,
            "representatives":len(valid),
            "min_edge":[] if not valid else list(valid[0][1]),
            "objective":None if min_cost is None else min_cost+a.score_weight*sc,
        })

    structural=sorted(rows,key=lambda r:(r["score"],r["qchild"]))
    compiled=[r for r in rows if r["min_official_cost"] is not None]
    pure_cost=sorted(compiled,key=lambda r:(r["min_official_cost"],r["score"],r["qchild"]))
    objective=sorted(compiled,key=lambda r:(r["objective"],r["score"],r["qchild"]))
    struct_rank={tuple(r["qchild"]):i+1 for i,r in enumerate(structural)}
    obj_rank={tuple(r["qchild"]):i+1 for i,r in enumerate(objective)}

    def view(r):
        return {
            "qchild":r["qchild"],"score":r["score"],
            "min_official_cost":r["min_official_cost"],
            "objective":r["objective"],
            "structural_rank":struct_rank[tuple(r["qchild"])],
            "objective_rank":obj_rank.get(tuple(r["qchild"])),
            "representatives":r["representatives"],
            "min_edge":r["min_edge"],
        }
    sk=structural[:a.topk]; ok=objective[:a.topk]; pk=pure_cost[:a.topk]
    ss={tuple(r["qchild"]) for r in sk}; os={tuple(r["qchild"]) for r in ok}
    ps={tuple(r["qchild"]) for r in pk}
    report={
        "schema":"acc-charged-selector-root-ab-v1",
        "challenge_id":a.target_id,
        "raw_children":len(raw),"unique_children":len(rows),
        "compiled_children":len(compiled),"children_without_official_rep":no_rep,
        "official_representatives_replayed":replayed,
        "topk":a.topk,"score_weight":a.score_weight,
        "structural_vs_objective_overlap":len(ss & os),
        "structural_vs_pure_cost_overlap":len(ss & ps),
        "structural_topk":[view(r) for r in sk],
        "objective_topk":[view(r) for r in ok],
        "pure_cost_topk":[view(r) for r in pk],
        "all_compiled":[view(r) for r in objective],
        "authority":{
            "official_repo":"SAIRcompetition/Andrews-Curtis",
            "official_commit":"99a65377c5c4f412cd9af7b8d31c41464a855736",
            "acsolverx_repo":"Avi161/ACSolverX",
            "acsolverx_commit":"5ae1bd8eda6d80dfbea51680636f825da19fb802",
            "search_base":"37893e3b940cb5d826b776b4aada385c8edd4de4"
        }
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("ACC_SELECTOR_AB",json.dumps({k:report[k] for k in (
        "challenge_id","raw_children","unique_children","compiled_children",
        "children_without_official_rep","official_representatives_replayed",
        "structural_vs_objective_overlap","structural_vs_pure_cost_overlap"
    )},sort_keys=True))
    print("STRUCTURAL_COSTS",[r["min_official_cost"] for r in sk])
    print("OBJECTIVE_COSTS",[r["min_official_cost"] for r in ok])
    print("STRUCTURAL_OBJECTIVE_RANKS",[obj_rank.get(tuple(r["qchild"])) for r in sk])

if __name__=="__main__":
    main()

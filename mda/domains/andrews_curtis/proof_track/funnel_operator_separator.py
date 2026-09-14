#!/usr/bin/env python3
from __future__ import annotations
import argparse, itertools, json, sys
from pathlib import Path

FROZEN_IDS=["ac-01684","ac-08027","ac-00106","ac-01523","ac-01520"]
LETTERS=(1,-1,2,-2)

def reduced_words(max_len):
    yield ()
    layer=[()]
    for _ in range(max_len):
        nxt=[]
        for p in layer:
            for a in LETTERS:
                if p and p[-1]==-a:
                    continue
                q=p+(a,)
                yield q
                nxt.append(q)
        layer=nxt

def conj_move(rel,g):
    order={1:0,-1:1,2:2,-2:3}
    return (6 if rel==0 else 10)+order[g]

def conj_path(rel,w):
    return tuple(conj_move(rel,g) for g in reversed(tuple(w)))

def replay(core,state,path):
    s=state
    peak=sum(map(len,s))
    for m in path:
        s=core.apply_move(s,m)
        peak=max(peak,sum(map(len,s)))
    return s,peak

def left_mul_path(core,state,i,j):
    mul=2 if i==0 else 4
    source=state[j]
    seq=(mul,)+conj_path(i,source)
    end,_=replay(core,state,seq)
    return seq,end

def funnel_path(core,state,i,w):
    j=1-i
    seq=[]
    s=state

    p,s=left_mul_path(core,s,i,j)
    seq.extend(p)

    p=conj_path(j,w)
    s,_=replay(core,s,p)
    seq.extend(p)

    invj=(j,)
    s,_=replay(core,s,invj)
    seq.extend(invj)

    p,s=left_mul_path(core,s,i,j)
    seq.extend(p)

    s,_=replay(core,s,invj)
    seq.extend(invj)

    winv=core.invert(tuple(w))
    p=conj_path(j,winv)
    s,peak_last=replay(core,s,p)
    seq.extend(p)

    end,peak=replay(core,state,tuple(seq))
    assert end==s
    return tuple(seq),end,peak

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--max-w-len",type=int,default=4)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[4]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import load_gssub,gssub_key,compiled_superneighbors,total_len
    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    by={c["challenge_id"]:c for c in manifest["challenges"]}
    limits=manifest["limits"]
    ns=load_gssub(Path(a.acsolverx_root))
    ws=list(reduced_words(a.max_w_len))

    rows=[]
    for cid in FROZEN_IDS:
        c=by[cid]
        initial=tuple(tuple(w) for w in c["initial_relators"])
        initial_total=total_len(initial)
        qcap=min(100,max(initial_total+36,48))

        base=compiled_superneighbors(core,ns,initial,qcap)
        base_states=[v[0] for v in base.values()]
        base_keys=set(base.keys())
        base_best=min([total_len(s) for s in base_states] or [initial_total])

        cands=[]
        for i in (0,1):
            for w in ws:
                if not w:
                    continue
                path,end,peak=funnel_path(core,initial,i,w)
                if peak>limits["max_total_relator_length"]:
                    continue
                # theorem-level operator must leave the other relator exact
                if end[1-i] != initial[1-i]:
                    raise RuntimeError(("source not restored",cid,i,w))
                key=gssub_key(ns,end)
                cands.append({
                    "i":i,"w":list(w),"w_len":len(w),
                    "atomic_cost":len(path),"path":list(path),
                    "end":[list(end[0]),list(end[1])],
                    "end_total":total_len(end),"peak":peak,
                    "key":list(key),
                    "novel_vs_gssub_one_step":key not in base_keys,
                })
        cands.sort(key=lambda z:(z["end_total"],z["atomic_cost"],z["i"],z["w"]))
        best=cands[0]
        rec={
            "challenge_id":cid,
            "initial_total":initial_total,
            "qcap":qcap,
            "candidate_count":len(cands),
            "baseline_gssub_neighbor_count":len(base),
            "baseline_best_one_step_total":base_best,
            "best_funnel":best,
            "strict_local_gain_vs_initial":initial_total-best["end_total"],
            "strict_gain_vs_best_gssub_one_step":base_best-best["end_total"],
            "separator":bool(best["end_total"]<base_best and best["novel_vs_gssub_one_step"]),
        }
        rows.append(rec)
        print("FUNNEL_SEPARATOR_CASE",json.dumps({
            "challenge_id":cid,
            "initial_total":initial_total,
            "baseline_best":base_best,
            "funnel_best":best["end_total"],
            "gain_vs_baseline":base_best-best["end_total"],
            "w":best["w"],"i":best["i"],
            "atomic_cost":best["atomic_cost"],
            "novel":best["novel_vs_gssub_one_step"],
            "separator":rec["separator"],
        },sort_keys=True),flush=True)

    report={
        "experiment":"ACC_FUNNEL_OPERATOR_SEPARATOR_V1",
        "frozen_residuals":FROZEN_IDS,
        "candidate_grammar":f"all freely reduced rank-2 words of length 1..{a.max_w_len}",
        "selection_rule":"minimize resulting exact total relator length; then atomic macro cost; then deterministic i,w order",
        "cases":len(rows),
        "separators":sum(r["separator"] for r in rows),
        "strict_local_gains":sum(r["strict_local_gain_vs_initial"]>0 for r in rows),
        "total_gain_vs_best_gssub_one_step":sum(max(0,r["strict_gain_vs_best_gssub_one_step"]) for r in rows),
        "status":"CERTIFIED_FUNNEL_LANGUAGE_SEPARATOR" if any(r["separator"] for r in rows) else "NO_LOCAL_SEPARATOR_IN_FROZEN_W_BOUND",
        "claim_boundary":"Local transition-language separator only. No end-to-end solver gain is claimed until a frozen downstream search test succeeds.",
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"cases.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print("FUNNEL_SEPARATOR_SUMMARY",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()

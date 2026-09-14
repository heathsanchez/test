#!/usr/bin/env python3
"""Exact nearest-conjugate projection induced by the proved AC funnel law.

For a state (A,B), funnel contraction with conjugator w replaces A by

    (w B w^-1)^-1 B A.

Thus the shortest possible funnel image is obtained by the conjugate C of B
nearest to D = B A in the free-group word metric.

If B = p c p^-1 with c cyclically reduced, every reduced conjugate is
r c' r^-1 for a cyclic rotation c' of c.  If r diverges from D before the
end of r, its distance to D is strictly worse than using a shortest cyclic
representative.  Hence an optimum has r equal to a prefix of D.

The search is therefore finite:
  prefixes(D) x cyclic rotations(c).

No conjugator-length bound is used.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

FROZEN_IDS=["ac-01684","ac-08027","ac-00106","ac-01523","ac-01520"]
POSITIVE_CONTROL=(
    (1,-2,-2,-1,2,2,2),
    (-2,-2,-2,-2,-2,-2,-2,-1),
)

def red(w):
    out=[]
    for a in w:
        if out and out[-1]==-a: out.pop()
        else: out.append(a)
    return tuple(out)

def inv(w): return tuple(-a for a in reversed(tuple(w)))

def cyclic_decompose(w):
    z=list(red(w)); p=[]
    while len(z)>=2 and z[0]==-z[-1]:
        p.append(z[0]); z=z[1:-1]
    return tuple(p),tuple(z)

def rotations(c):
    if not c:
        return [((),())]
    out=[];seen=set()
    for t in range(len(c)):
        u=c[:t]
        r=c[t:]+c[:t]
        if r in seen: continue
        seen.add(r);out.append((u,r))
    return out

def nearest_conjugate(B,D):
    B=red(B);D=red(D)
    p,c=cyclic_decompose(B)
    best=None;all_best=[]
    for qlen in range(len(D)+1):
        q=D[:qlen]
        for u,crot in rotations(c):
            C=red(q+crot+inv(q))
            y=red(inv(C)+D)
            # B = p c p^-1 and crot = u^-1 c u, hence
            # C = w B w^-1 for w = q u^-1 p^-1.
            w=red(q+inv(u)+inv(p))
            rec={
                "w":w,"C":C,"y":y,
                "distance":len(y),
                "conjugate_length":len(C),
                "q_len":qlen,"rotation_split":len(u),
            }
            key=(len(y),len(w),len(C),w,C)
            if best is None or key<best:
                best=key;all_best=[rec]
            elif key==best:
                all_best.append(rec)
    return all_best[0],all_best

def project_state(state,i):
    A=tuple(state[i]);B=tuple(state[1-i])
    D=red(B+A)
    best,ties=nearest_conjugate(B,D)
    end=list(state);end[i]=best["y"];end=tuple(end)
    return end,best,ties

def conj_move(rel,g):
    order={1:0,-1:1,2:2,-2:3}
    return (6 if rel==0 else 10)+order[g]

def conj_path(rel,w):
    return tuple(conj_move(rel,g) for g in reversed(tuple(w)))

def replay(core,state,path):
    s=state;peak=sum(map(len,s))
    for m in path:
        s=core.apply_move(s,m);peak=max(peak,sum(map(len,s)))
    return s,peak

def left_mul(core,state,i,j):
    mul=2 if i==0 else 4
    p=(mul,)+conj_path(i,state[j])
    end,_=replay(core,state,p)
    return p,end

def compile_projection(core,state,i,w):
    j=1-i;seq=[];s=state
    p,s=left_mul(core,s,i,j);seq+=list(p)
    p=conj_path(j,w);s,_=replay(core,s,p);seq+=list(p)
    s,_=replay(core,s,(j,));seq.append(j)
    p,s=left_mul(core,s,i,j);seq+=list(p)
    s,_=replay(core,s,(j,));seq.append(j)
    p=conj_path(j,inv(w));s,_=replay(core,s,p);seq+=list(p)
    end,peak=replay(core,state,seq)
    assert end==s
    return tuple(seq),end,peak

def total(s): return sum(map(len,s))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    acc=Path(a.acc_root);sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    by={c["challenge_id"]:c for c in manifest["challenges"]}
    limits=manifest["limits"]

    cases=[("positive-control",POSITIVE_CONTROL)]
    for cid in FROZEN_IDS:
        cases.append((cid,tuple(tuple(w) for w in by[cid]["initial_relators"])))

    rows=[]
    for cid,state in cases:
        arms=[]
        for i in (0,1):
            end,best,ties=project_state(state,i)
            path,chk,peak=compile_projection(core,state,i,best["w"])
            if chk!=end:
                raise RuntimeError(("projection compiler mismatch",cid,i,best,end,chk))
            arms.append({
                "i":i,"initial_total":total(state),"end_total":total(end),
                "gain":total(state)-total(end),
                "w":list(best["w"]),"w_len":len(best["w"]),
                "nearest_conjugate":list(best["C"]),
                "projected_relator":list(best["y"]),
                "metric_distance":best["distance"],
                "tie_count":len(ties),
                "atomic_cost":len(path),"peak":peak,
                "path":list(path),
            })
        arms.sort(key=lambda z:(-z["gain"],z["atomic_cost"],z["i"],z["w"]))
        best=arms[0]
        rec={"challenge_id":cid,"best":best,"arms":arms}
        rows.append(rec)
        print("NEAREST_CONJUGATE_CASE",json.dumps({
            "challenge_id":cid,"initial_total":best["initial_total"],
            "end_total":best["end_total"],"gain":best["gain"],
            "i":best["i"],"w":best["w"],"w_len":best["w_len"],
            "atomic_cost":best["atomic_cost"],"peak":best["peak"],
        },sort_keys=True),flush=True)

    positive=rows[0]
    if positive["best"]["gain"] <= 0:
        raise RuntimeError("positive funnel control was not recovered")

    hard=rows[1:]
    report={
        "experiment":"ACC_EXACT_NEAREST_CONJUGATE_FUNNEL_V1",
        "status":"VERIFIED_EXACT_FUNNEL_PROJECTION_CENSUS",
        "candidate_space":"all conjugates, reduced exactly to prefixes(D) x cyclic rotations(cyclic_core(B))",
        "positive_control_gain":positive["best"]["gain"],
        "hard_cases":len(hard),
        "hard_immediate_gains":sum(r["best"]["gain"]>0 for r in hard),
        "hard_ties":sum(r["best"]["gain"]==0 for r in hard),
        "hard_worsenings":sum(r["best"]["gain"]<0 for r in hard),
        "claim_boundary":"Exact nearest-conjugate projection under the stated free-group lemma; official move replay validates every selected macro. End-to-end search value is separate.",
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"cases.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print("NEAREST_CONJUGATE_SUMMARY",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()

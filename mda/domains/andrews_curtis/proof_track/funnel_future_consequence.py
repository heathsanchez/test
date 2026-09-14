#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, importlib.util, json, sys
from pathlib import Path

FROZEN_IDS=["ac-01684","ac-08027","ac-00106","ac-01523","ac-01520"]

def load_separator_module(path):
    spec=importlib.util.spec_from_file_location("fos",path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def horizon(ns,state,depth,max_len,node_cap=100000):
    reduce_relator=ns["reduce_relator_nj"]
    canonical_pair=ns["canonical_pair_nj"]
    state_to_key=ns["state_to_key"]
    str_to_arr=ns["str_to_arr"]
    get_neighbors=ns["get_neighbors_nj"]

    def exact_to_key(s):
        a=reduce_relator(str_to_arr("".join({1:"x",-1:"X",2:"y",-2:"Y"}[z] for z in s[0])))
        b=reduce_relator(str_to_arr("".join({1:"x",-1:"X",2:"y",-2:"Y"}[z] for z in s[1])))
        return state_to_key(canonical_pair(a,b))

    k0=exact_to_key(state)
    q=collections.deque([(k0,0)])
    seen={k0}
    best=(len(k0[0])+len(k0[1]),0,k0)
    nodes=0
    while q and nodes<node_cap:
        key,d=q.popleft();nodes+=1
        score=len(key[0])+len(key[1])
        if (score,d,key)<best: best=(score,d,key)
        if d>=depth: continue
        a,b=(str_to_arr(key[0]),str_to_arr(key[1]))
        for na,nb in get_neighbors(a,b):
            ra,rb=reduce_relator(na),reduce_relator(nb)
            if len(ra)+len(rb)>=max_len: continue
            ca,cb=canonical_pair(ra,rb)
            nk=state_to_key((ca,cb))
            if nk in seen: continue
            seen.add(nk);q.append((nk,d+1))
    return {"best_total":best[0],"best_depth":best[1],"nodes":nodes,"seen":len(seen),"capped":nodes>=node_cap}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--separator-script",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--max-w-len",type=int,default=4)
    a=ap.parse_args()

    fos=load_separator_module(Path(a.separator_script))
    root=Path(__file__).resolve().parents[4]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import load_gssub,total_len
    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    by={c["challenge_id"]:c for c in manifest["challenges"]}
    limits=manifest["limits"]
    ns=load_gssub(Path(a.acsolverx_root))
    ws=[w for w in fos.reduced_words(a.max_w_len) if w]

    rows=[]
    cache={}
    def H(state,d,qcap):
        key=(state,d,qcap)
        if key not in cache: cache[key]=horizon(ns,state,d,qcap)
        return cache[key]

    for cid in FROZEN_IDS:
        c=by[cid]
        initial=tuple(tuple(w) for w in c["initial_relators"])
        initial_total=total_len(initial)
        qcap=min(100,max(initial_total+36,48))
        base=H(initial,3,qcap)

        cs=[]
        for i in (0,1):
            for w in ws:
                path,end,peak=fos.funnel_path(core,initial,i,w)
                if peak>limits["max_total_relator_length"]: continue
                fut=H(end,2,qcap)
                cs.append({
                    "i":i,"w":list(w),"atomic_cost":len(path),
                    "end_total":total_len(end),"future2":fut,
                    "path":list(path),"end":[list(end[0]),list(end[1])],
                })
        cs.sort(key=lambda z:(z["future2"]["best_total"],z["future2"]["best_depth"],
                              z["atomic_cost"],z["end_total"],z["i"],z["w"]))
        best=cs[0]
        winners=[z for z in cs if z["future2"]["best_total"]==best["future2"]["best_total"]]
        sep=best["future2"]["best_total"]<base["best_total"]
        rec={
          "challenge_id":cid,"initial_total":initial_total,"qcap":qcap,
          "baseline_horizon3":base,
          "candidate_count":len(cs),
          "best_funnel_plus_horizon2":best,
          "minimum_future_total":best["future2"]["best_total"],
          "minimum_winner_count":len(winners),
          "future_gain":base["best_total"]-best["future2"]["best_total"],
          "separator":sep,
        }
        rows.append(rec)
        print("FUNNEL_FUTURE_CASE",json.dumps({
          "challenge_id":cid,
          "baseline_h3":base["best_total"],
          "funnel_h2":best["future2"]["best_total"],
          "gain":rec["future_gain"],"separator":sep,
          "i":best["i"],"w":best["w"],
          "macro_atomic_cost":best["atomic_cost"],
          "end_total":best["end_total"],
          "baseline_nodes":base["nodes"],
          "funnel_future_nodes":best["future2"]["nodes"],
        },sort_keys=True),flush=True)

    report={
      "experiment":"ACC_FUNNEL_FUTURE_CONSEQUENCE_V1",
      "frozen_residuals":FROZEN_IDS,
      "candidate_grammar":f"all freely reduced rank-2 words length 1..{a.max_w_len}",
      "baseline":"best canonical total within <=3 unchanged GS-Sub layers",
      "funnel_arm":"one exact theorem-derived funnel macro, then <=2 unchanged GS-Sub layers",
      "selection":"candidate set frozen before future-consequence evaluation; retain all minimum-future candidates",
      "cases":len(rows),
      "separators":sum(r["separator"] for r in rows),
      "total_future_gain":sum(max(0,r["future_gain"]) for r in rows),
      "status":"VERIFIED_FUNNEL_FUTURE_SEPARATOR" if any(r["separator"] for r in rows) else "NO_FUNNEL_FUTURE_SEPARATOR_H3",
      "claim_boundary":"Bounded quotient-future discriminator only; no end-to-end certificate claim.",
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"cases.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print("FUNNEL_FUTURE_SUMMARY",json.dumps(report,sort_keys=True))

if __name__=="__main__":main()

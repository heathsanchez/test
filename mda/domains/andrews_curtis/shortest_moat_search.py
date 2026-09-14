#!/usr/bin/env python3
"""Targeted bounded shortest-proof search for one ACC presentation.

The live record is frozen first.  A strict steal requires a certificate of at
most live_best-1 official moves.  Search uses the exact compiled GS-Sub
transition language and exact official move costs, but can choose either:

  baseline: current GS-Sub quotient identity
  refined:  (GS-Sub quotient, learned S2-invariant rotation-orbit code)

A reverse exact atlas supplies suffixes to the target.  A modular quotient
distance is used only as an admissible lower bound.  Every returned path is
replayed by the pinned official verifier.
"""
from __future__ import annotations
import argparse, collections, heapq, json, sys, time
from pathlib import Path

TARGET=((1,),(2,))

def save(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--challenge-id",required=True)
    ap.add_argument("--live-best",type=int,required=True)
    ap.add_argument("--identity",choices=["baseline","refined"],required=True)
    ap.add_argument("--node-cap",type=int,default=500000)
    ap.add_argument("--reverse-depth",type=int,default=8)
    ap.add_argument("--reverse-cap",type=int,default=750000)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse, challenge_maps, compiled_superneighbor_candidates,
        compiled_superneighbors, gssub_key, int_word_to_str, load_gssub,
        orientation_options, total_len,
    )
    sys.path.insert(0,str(root/"acc_competitive"))
    from proof_atlas_fortify_v1 import mod_state, modular_pdb

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]
    ac,_=challenge_maps(manifest)
    c=ac[a.challenge_id]
    initial=tuple(tuple(w) for w in c["initial_relators"])
    ns=load_gssub(Path(a.acsolverx_root))
    strict_bound=a.live_best-1

    # Exact reverse suffixes. No representation abstraction here.
    t0=time.time()
    reverse,rev_meta=build_reverse(
        core,a.reverse_depth,a.reverse_cap,
        max_total=limits["max_total_relator_length"],
    )
    reverse_build_s=time.time()-t0

    # Precompute small modular PDBs; these are lower bounds only.
    primes=(2,3,5,7,11,13)
    pdb={p:modular_pdb(p) for p in primes}
    def lb(st):
        best=0
        for p in primes:
            d=pdb[p].get(mod_state(st,p))
            if d is not None and d>best: best=d
        return best

    def rot_code(st,qkey):
        opts=[]
        for i in (0,1):
            z=[]
            for w,seq in orientation_options(core,st[i],i):
                s=int_word_to_str(w)
                inv=bool(seq and seq[0]==i)
                rot=len(seq)-(1 if inv else 0)
                z.append((s,int(rot),len(seq)))
            opts.append(z)
        cand=[]
        for slot0 in (0,1):
            slot1=1-slot0
            m0=[x for x in opts[0] if x[0]==qkey[slot0]]
            m1=[x for x in opts[1] if x[0]==qkey[slot1]]
            for x in m0:
                for y in m1:
                    cand.append((x[2]+y[2],tuple(sorted((x[1],y[1])))))
        if not cand: raise RuntimeError("rot coordinate unavailable")
        cand.sort()
        return cand[0][1]

    def ident(st):
        q=gssub_key(ns,st)
        if a.identity=="baseline": return ("Q",q)
        return ("QR",q,rot_code(st,q))

    def neighbors(st):
        # Transition language identical across arms.
        legacy=compiled_superneighbors(core,ns,st,limits["max_total_relator_length"])
        by={}
        for desired,hit0 in legacy.items():
            xs=compiled_superneighbor_candidates(
                core,ns,st,desired,limits["max_total_relator_length"]
            )
            if not xs: xs=[hit0]
            for n,e in xs:
                e=tuple(e)
                old=by.get(n)
                if old is None or len(e)<len(old): by[n]=e
        return list(by.items())

    k0=ident(initial)
    best={k0:0}; states={k0:initial}; parent={k0:None}; pedge={}
    h0=lb(initial)
    pq=[(h0,0,0,k0)]
    serial=1; popped=0; generated=0; pruned_bound=0; pruned_seen=0
    goal=None; goal_suffix=None; goal_cost=None
    start=time.time()

    while pq and popped<a.node_cap:
        f,g,_,k=heapq.heappop(pq)
        if g!=best.get(k): continue
        st=states[k]
        if g+lb(st)>strict_bound:
            pruned_bound+=1
            continue
        popped+=1

        suf=reverse.get(st)
        if suf is not None and g+len(suf)<=strict_bound:
            goal=k;goal_suffix=tuple(suf);goal_cost=g+len(suf);break
        if st==TARGET and g<=strict_bound:
            goal=k;goal_suffix=();goal_cost=g;break

        for n,e in neighbors(st):
            generated+=1
            ng=g+len(e)
            nh=lb(n)
            if ng+nh>strict_bound:
                pruned_bound+=1
                continue
            nk=ident(n)
            if ng>=best.get(nk,10**18):
                pruned_seen+=1
                continue
            best[nk]=ng;states[nk]=n;parent[nk]=k;pedge[nk]=e
            heapq.heappush(pq,(ng+nh,ng,serial,nk));serial+=1

    path=None; verdict=None
    if goal is not None:
        edges=[];cur=goal
        while parent[cur] is not None:
            edges.append(pedge[cur]);cur=parent[cur]
        edges.reverse()
        path=tuple(m for e in edges for m in e)+tuple(goal_suffix)
        verdict=core.verify(c,list(path),c["move_spec_version"],limits)
        if not verdict.get("ok"):
            raise RuntimeError(verdict)
        if len(path)>strict_bound:
            raise RuntimeError(("bound violation",len(path),strict_bound))

    out={
      "experiment":"ACC_MDA_AC04359_SHORTEST_MOAT_SEARCH_V1",
      "challenge_id":a.challenge_id,
      "identity":a.identity,
      "live_best_frozen":a.live_best,
      "strict_bound":strict_bound,
      "status":"VERIFIED_STRICT_RECORD_CANDIDATE" if path is not None else (
          "UNKNOWN_SEARCH_NODE_CAP" if popped>=a.node_cap else "NO_STRICT_PATH_IN_EXPLORED_SEARCH"
      ),
      "found":path is not None,
      "length":None if path is None else len(path),
      "certificate":None if path is None else list(path),
      "certificate_hash":None if verdict is None else verdict.get("certificate_hash"),
      "nodes_popped":popped,
      "neighbors_generated":generated,
      "identity_states":len(best),
      "pruned_bound":pruned_bound,
      "pruned_seen":pruned_seen,
      "reverse_states":len(reverse),
      "reverse_meta":rev_meta,
      "reverse_build_s":round(reverse_build_s,3),
      "elapsed_s":round(time.time()-start,3),
      "node_cap":a.node_cap,
      "claim_boundary":"Strict < frozen live record only; exact official replay; result is not a shortestness proof unless exhaustive status is separately established.",
    }
    outdir=Path(a.out_dir);outdir.mkdir(parents=True,exist_ok=True)
    save(outdir/"result.json",out)
    if path is not None:
        (outdir/"candidate.txt").write_text(
            f"{a.challenge_id}: {json.dumps(list(path),separators=(',',':'))}\n"
        )
    else:
        (outdir/"candidate.txt").write_text("")
    print("MDA_MOAT_SEARCH",json.dumps({
      "identity":a.identity,"status":out["status"],"found":out["found"],
      "length":out["length"],"nodes":popped,"states":len(best),
      "reverse_states":len(reverse),"elapsed_s":out["elapsed_s"],
    },sort_keys=True),flush=True)

if __name__=="__main__":
    main()

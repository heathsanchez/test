#!/usr/bin/env python3
"""
ACC causal representation experiment.

Frozen learned distinction: S2-invariant cyclic-rotation orbit ("rot"), selected
prospectively by prior runs. This script changes only state identity in an exact
GS-Sub compiled search:

  baseline key = current GS-Sub quotient
  refined  key = (current GS-Sub quotient, learned rot-orbit code)

Transitions, priority, node budget, compiler, target, verifier, and limits are
identical. The search emits official atomic move certificates and verifies them
with the pinned ACC verifier.

Mode select:
  deterministically scan fresh official challenges, baseline only, and freeze a
  batch of baseline-solvable targets before refined outcomes are evaluated.

Mode evaluate:
  rerun the frozen targets under baseline (ablation/replay) and refined keys,
  compare exact verified certificate lengths, and type the causal result.
"""
from __future__ import annotations

import argparse, hashlib, heapq, json, sys, time
from pathlib import Path

TARGET=((1,),(2,))
USED={
 "ac-04402","ac-02012","ac-09722","ac-05232","ac-02616","ac-08534",
 "ac-08857","ac-02940","ac-08551","ac-03392","ac-04629","ac-06598",
}

def save(p,obj):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

def bootstrap(a):
    root=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse, challenge_maps, compiled_superneighbor_candidates,
        compiled_superneighbors, exact_terminal_suffix, gssub_key,
        int_word_to_str, load_gssub, orientation_options, total_len,
    )
    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition"/"tools"))
    from verifier import core
    manifest=json.loads((acc/"competition"/"tools"/"verifier"/"data"/"manifest.json").read_text())
    limits=manifest["limits"]
    ac,_=challenge_maps(manifest)
    ns=load_gssub(Path(a.acsolverx_root))
    rev=build_reverse(core,a.reverse_depth,a.reverse_cap,max_total=20)[0]
    return locals()

def rot_orbit_code(core,ns,orientation_options,int_word_to_str,state,qkey):
    opts=[]
    for i in (0,1):
        z=[]
        for w,seq in orientation_options(core,state[i],i):
            s=int_word_to_str(w)
            inv=bool(seq and seq[0]==i)
            rot=len(seq)-(1 if inv else 0)
            z.append((s,rot,len(seq)))
        opts.append(z)
    assignments=[]
    for slot0 in (0,1):
        slot1=1-slot0
        for a0 in [x for x in opts[0] if x[0]==qkey[slot0]]:
            for a1 in [x for x in opts[1] if x[0]==qkey[slot1]]:
                code=tuple(sorted((int(a0[1]),int(a1[1]))))
                assignments.append((a0[2]+a1[2],code))
    if not assignments:
        raise RuntimeError("cannot recover rot orbit coordinate")
    assignments.sort()
    return assignments[0][1]

def search(env,cid,mode,max_nodes):
    core,ns,limits=env["core"],env["ns"],env["limits"]
    c=env["ac"][cid]
    exact=tuple(tuple(w) for w in c["initial_relators"])
    total_len=env["total_len"]
    gssub_key=env["gssub_key"]
    comp=env["compiled_superneighbors"]
    cands=env["compiled_superneighbor_candidates"]
    term=env["exact_terminal_suffix"]

    def ident(st):
        q=gssub_key(ns,st)
        if mode=="baseline":
            return ("Q",q)
        r=rot_orbit_code(core,ns,env["orientation_options"],env["int_word_to_str"],st,q)
        return ("QR",q,r)

    def neigh(st):
        # Same transition generator for both arms. Enumerate every exact compiled
        # representative produced for each current quotient neighbor.
        desired=list(comp(core,ns,st,limits["max_total_relator_length"]).keys())
        by={}
        for q in desired:
            xs=cands(core,ns,st,q,limits["max_total_relator_length"])
            if not xs:
                hit=comp(core,ns,st,limits["max_total_relator_length"]).get(q)
                xs=[] if hit is None else [hit]
            for n,e in xs:
                e=tuple(e)
                old=by.get(n)
                if old is None or len(e)<len(old):
                    by[n]=e
        return list(by.items())

    k0=ident(exact)
    best={k0:0}; states={k0:exact}; parent={k0:None}; pedge={}
    # Identical search priority in both arms.
    pq=[(2*total_len(exact),0,0,k0)]
    serial=1; popped=0; generated=0; max_frontier=1
    t0=time.time()
    goal=None; suffix=()
    while pq and popped<max_nodes:
        pri,g,_,k=heapq.heappop(pq)
        if g!=best.get(k): continue
        st=states[k]; popped+=1
        if st==TARGET:
            goal=k; suffix=(); break
        q=gssub_key(ns,st)
        if len(q[0])==1 and len(q[1])==1:
            s=term(core,st,env["rev"])
            if s is not None:
                goal=k; suffix=tuple(s); break
        for n,e in neigh(st):
            generated+=1
            nk=ident(n); ng=g+len(e)
            if ng>=best.get(nk,10**18): continue
            best[nk]=ng; states[nk]=n; parent[nk]=k; pedge[nk]=e
            h=2*total_len(n)
            heapq.heappush(pq,(ng+h,ng,serial,nk)); serial+=1
        max_frontier=max(max_frontier,len(pq))
    elapsed=time.time()-t0
    atomics=None; verdict=None
    if goal is not None:
        edges=[]
        cur=goal
        while parent[cur] is not None:
            edges.append(pedge[cur]); cur=parent[cur]
        edges.reverse()
        atomics=tuple(x for e in edges for x in e)+suffix
        verdict=core.verify(c,list(atomics),c["move_spec_version"],limits)
        if not verdict["ok"]:
            raise RuntimeError((cid,mode,"official verify failed",verdict))
    return {
      "challenge_id":cid,"mode":mode,"solved":atomics is not None,
      "verified":bool(verdict and verdict["ok"]),
      "atomic_length":None if atomics is None else len(atomics),
      "certificate":None if atomics is None else list(atomics),
      "certificate_hash":None if verdict is None else verdict.get("certificate_hash"),
      "nodes_popped":popped,"neighbors_generated":generated,
      "identity_states":len(best),"max_frontier":max_frontier,
      "elapsed_s":round(elapsed,3),"node_budget":max_nodes,
      "initial_total":total_len(exact),
    }

def select(a,env):
    rows=[]
    for cid,c in env["ac"].items():
        if cid in USED: continue
        total=sum(len(w) for w in c["initial_relators"])
        rows.append((total,cid))
    rows.sort()
    attempts=[]; frozen=[]
    for total,cid in rows[:a.candidate_scan]:
        r=search(env,cid,"baseline",a.max_nodes)
        attempts.append(r)
        print("BASELINE_SCAN",json.dumps({k:r[k] for k in ("challenge_id","solved","atomic_length","nodes_popped","elapsed_s")}),flush=True)
        if r["verified"]:
            frozen.append(r)
            if len(frozen)>=a.freeze_count: break
    status="FROZEN_BASELINE_BATCH" if len(frozen)>=a.freeze_count else "UNKNOWN_SEARCH_INSUFFICIENT_BASELINES"
    out={
      "experiment":"ACC_MDA_LEARNED_REPRESENTATION_CAUSAL_V1_FREEZE",
      "status":status,
      "selection_rule":"smallest initial-total official AC challenges, then challenge_id, excluding all representation-development targets; retain first baseline-verified cases",
      "representation_winner_source_run":34823252091,
      "frozen_representation":"S2-invariant cyclic-rotation orbit code (rot)",
      "refined_outcomes_observed":False,
      "max_nodes":a.max_nodes,"candidate_scan":a.candidate_scan,
      "frozen_targets":frozen,"attempts":attempts,
    }
    save(Path(a.out_dir)/"baseline_freeze.json",out)
    print("MDA_CAUSAL_FREEZE",json.dumps({"status":status,"targets":[x["challenge_id"] for x in frozen]},sort_keys=True))

def evaluate(a,env):
    frozen=json.loads(Path(a.baseline_freeze).read_text())
    if frozen["status"]!="FROZEN_BASELINE_BATCH":
        raise SystemExit("baseline freeze incomplete")
    results=[]
    for b0 in frozen["frozen_targets"]:
        cid=b0["challenge_id"]
        # Exact baseline replay is the causal ablation. Same deterministic code,
        # same budget, now run beside the refined arm.
        abl=search(env,cid,"baseline",frozen["max_nodes"])
        ref=search(env,cid,"refined",frozen["max_nodes"])
        assert abl["verified"] and abl["atomic_length"]==b0["atomic_length"],(cid,b0,abl)
        delta=None if not ref["verified"] else b0["atomic_length"]-ref["atomic_length"]
        rec={"challenge_id":cid,"frozen_baseline":b0,"ablation_replay":abl,"refined":ref,"saving":delta}
        results.append(rec)
        print("MDA_CAUSAL_CASE",json.dumps({"cid":cid,"baseline":b0["atomic_length"],"refined":ref["atomic_length"],"saving":delta},sort_keys=True),flush=True)

    solved=[r for r in results if r["refined"]["verified"]]
    improved=[r for r in solved if r["saving"]>0]
    equal=[r for r in solved if r["saving"]==0]
    worse=[r for r in solved if r["saving"]<0]
    if not solved:
        status="UNKNOWN_SEARCH_REFINED"
    elif len(improved)>=2:
        status="VERIFIED_TRANSFERRED_CAUSAL_REPRESENTATION_GAIN"
    elif len(improved)==1:
        status="VERIFIED_SINGLE_CAUSAL_REPRESENTATION_GAIN"
    else:
        status="VALID_NEGATIVE_NO_CAUSAL_GAIN"

    out={
      "experiment":"ACC_MDA_LEARNED_REPRESENTATION_CAUSAL_V1",
      "status":status,
      "frozen_representation":"S2-invariant cyclic-rotation orbit code (rot)",
      "only_intervention":"state identity: quotient -> (quotient,rot); transitions/priority/node budget/compiler/verifier unchanged",
      "cases":results,
      "refined_solved":len(solved),"strict_improvements":len(improved),
      "ties":len(equal),"regressions":len(worse),
      "total_atomic_saving":sum(r["saving"] for r in solved if r["saving"] is not None),
      "causal_ablation_pass":all(r["ablation_replay"]["atomic_length"]==r["frozen_baseline"]["atomic_length"] for r in results),
      "transfer_pass":len(improved)>=2,
      "global_inheritance_authorized":False,
      "next_probe":(
        "If causal gain: run one further untouched target using rot without reacquisition, then consider scoped integration. "
        "If no gain: preserve the representational separator but reject search integration in this form."
      ),
      "claim_boundary":"Fresh official ACC targets selected and baseline-frozen before refined outcomes; bounded matched-budget exact compiled search only."
    }
    save(Path(a.out_dir)/"result.json",out)
    lines=[]
    for r in improved:
        cid=r["challenge_id"]; cert=r["refined"]["certificate"]
        lines.append(f"{cid}: {json.dumps(cert,separators=(',',':'))}")
    (Path(a.out_dir)/"improved_submission.txt").write_text("\n".join(lines)+("\n" if lines else ""))
    print("MDA_CAUSAL_SYNTHESIS",json.dumps({k:out[k] for k in ("status","refined_solved","strict_improvements","ties","regressions","total_atomic_saving","causal_ablation_pass","transfer_pass")},sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["select","evaluate"],required=True)
    p.add_argument("--acc-root",required=True); p.add_argument("--acsolverx-root",required=True)
    p.add_argument("--out-dir",required=True)
    p.add_argument("--baseline-freeze")
    p.add_argument("--max-nodes",type=int,default=5000)
    p.add_argument("--candidate-scan",type=int,default=16)
    p.add_argument("--freeze-count",type=int,default=4)
    p.add_argument("--reverse-depth",type=int,default=7)
    p.add_argument("--reverse-cap",type=int,default=150000)
    a=p.parse_args(); env=bootstrap(a)
    if a.mode=="select": select(a,env)
    else:
        if not a.baseline_freeze: raise SystemExit("--baseline-freeze required")
        evaluate(a,env)

if __name__=="__main__": main()

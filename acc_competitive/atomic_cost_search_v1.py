#!/usr/bin/env python3
from __future__ import annotations
import argparse, heapq, itertools, json, sys, time
from pathlib import Path

def save(p,o):
    Path(p).write_text(json.dumps(o,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--acsolverx-root",required=True)
    ap.add_argument("--target-id",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--snapshot-stable",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--alpha",type=float,required=True)
    ap.add_argument("--max-nodes",type=int,default=60000)
    ap.add_argument("--max-seconds",type=int,default=1500)
    ap.add_argument("--total-cap",type=int,default=100)
    ap.add_argument("--reverse-depth",type=int,default=7)
    ap.add_argument("--reverse-cap",type=int,default=250000)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import (
        build_reverse, challenge_maps, compiled_superneighbors, exact_terminal_suffix,
        gssub_key, load_gssub, snapshot_file_map, total_len,
    )

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core, stable_core

    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]
    ac_by,sac_by=challenge_maps(manifest)
    c=ac_by[a.target_id]
    initial=tuple(tuple(w) for w in c["initial_relators"])
    sid="sac-"+a.target_id[3:]
    sc=sac_by[sid]

    _,ac_live=snapshot_file_map(a.snapshot_ac)
    _,st_live=snapshot_file_map(a.snapshot_stable)
    live_ac=ac_live.get(a.target_id,{})
    live_st=st_live.get(sid,{})

    ns=load_gssub(Path(a.acsolverx_root))
    reverse_paths,reverse_hist=build_reverse(core,a.reverse_depth,a.reverse_cap)

    counter=itertools.count()
    ikey=gssub_key(ns,initial)
    # Best cost per quotient key, with the cheapest exact representative carried.
    best={ikey:0}
    parent={ikey:None}
    parent_edge={}
    exact={ikey:initial}

    def heuristic(state):
        # Atomic cost is the true competition objective. Total relator length
        # is only a search bias; alpha=0 is pure Dijkstra on compiled supermoves.
        return a.alpha*max(0,total_len(state)-2)

    pq=[(heuristic(initial),0,next(counter),ikey)]
    nodes=0
    start=time.time()
    goal_key=None
    goal_suffix=None

    while pq and nodes<a.max_nodes and time.time()-start<a.max_seconds:
        _,g,_,key=heapq.heappop(pq)
        if g!=best.get(key):
            continue
        state=exact[key]
        nodes+=1

        suffix=reverse_paths.get(state)
        if suffix is None and total_len(state)<=20:
            suffix=exact_terminal_suffix(core,state,reverse_paths)
        if suffix is not None:
            goal_key=key
            goal_suffix=tuple(suffix)
            break

        nbrs=compiled_superneighbors(core,ns,state,a.total_cap)
        for nkey,(nstate,edge) in nbrs.items():
            ng=g+len(edge)
            if ng>=best.get(nkey,10**18):
                continue
            best[nkey]=ng
            exact[nkey]=nstate
            parent[nkey]=key
            parent_edge[nkey]=tuple(edge)
            heapq.heappush(pq,(ng+heuristic(nstate),ng,next(counter),nkey))

    atomics=None
    if goal_key is not None:
        chunks=[]
        cur=goal_key
        while parent[cur] is not None:
            chunks.append(parent_edge[cur])
            cur=parent[cur]
        chunks.reverse()
        atomics=tuple(m for ch in chunks for m in ch)+tuple(goal_suffix or ())
        end=initial
        for m in atomics:
            end=core.apply_move(end,m)
        if end!=((1,),(2,)):
            raise RuntimeError(("atomic_search_bad_target",end))

    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    row={
      "experiment":"ACC_ATOMIC_COST_SEARCH_V1",
      "challenge_id":a.target_id,
      "stable_id":sid,
      "alpha":a.alpha,
      "max_nodes":a.max_nodes,
      "nodes":nodes,
      "elapsed_seconds":time.time()-start,
      "frontier_states":len(best),
      "found":atomics is not None,
      "live_ac_best":live_ac.get("currentBestLength"),
      "live_stable_best":live_st.get("currentBestLength"),
      "reverse_states":len(reverse_paths),
      "reverse_hist":reverse_hist,
    }
    if atomics is not None:
        v=core.verify(c,list(atomics),c["move_spec_version"],limits)
        stable=tuple(atomics)+(16,15)
        sv=stable_core.verify(sc,list(stable),sc["move_spec_version"],limits)
        row.update({
          "ac_verdict":v,"atomic_length":len(atomics),
          "stable_verdict":sv,"stable_length":len(stable),
          "strict_ac_frozen": isinstance(live_ac.get("currentBestLength"),int) and len(atomics)<live_ac["currentBestLength"],
          "tie_ac_frozen": isinstance(live_ac.get("currentBestLength"),int) and len(atomics)==live_ac["currentBestLength"],
          "strict_stable_frozen": isinstance(live_st.get("currentBestLength"),int) and len(stable)<live_st["currentBestLength"],
          "tie_stable_frozen": isinstance(live_st.get("currentBestLength"),int) and len(stable)==live_st["currentBestLength"],
        })
        if not v.get("ok") or not sv.get("ok"):
            raise RuntimeError(("verifier_failure",row))
        (out/"candidate_ac.txt").write_text(
          f"{a.target_id}: {json.dumps(list(atomics),separators=(',',':'))}\n",
          encoding="utf-8"
        )
    save(out/"result.json",row)
    print("ATOMIC_COST_RESULT",json.dumps(row,sort_keys=True))

if __name__=="__main__": main()

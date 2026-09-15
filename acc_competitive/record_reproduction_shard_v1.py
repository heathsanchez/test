#!/usr/bin/env python3
"""Sharded exact search to reproduce or beat a public ACC record length.

The public record supplies only a length threshold. No competitor certificate is
used. Search is exact in official atomic moves; the known 18-move path is used
only as a trajectory-shaped ordering heuristic, never as a pruning rule.
"""
from __future__ import annotations
import argparse, heapq, json, re, sys, time
from pathlib import Path

MAP={-2:1,-1:2,1:3,2:4}
UNMAP={1:-2,2:-1,3:1,4:2}

def parse(path,cid):
    for line in Path(path).read_text().splitlines():
        m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
        if m and m.group(1)==cid:return list(json.loads(m.group(2)))
    raise KeyError(cid)

def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])

def from_key(k):
    j=k.index(0)
    return (tuple(UNMAP[x] for x in k[:j]),tuple(UNMAP[x] for x in k[j+1:]))

def feat(s):
    def wf(w):
        ex1=sum(1 if x==1 else -1 if x==-1 else 0 for x in w)
        ex2=sum(1 if x==2 else -1 if x==-2 else 0 for x in w)
        turns=sum(1 for a,b in zip(w,w[1:]) if abs(a)!=abs(b))
        return (len(w),abs(ex1),abs(ex2),turns)
    a,b=sorted((wf(s[0]),wf(s[1])))
    return a+b+(len(s[0])+len(s[1]),)

def fd(a,b):
    return sum(abs(x-y) for x,y in zip(a,b))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--candidate-file",required=True)
    ap.add_argument("--challenge-id",required=True)
    ap.add_argument("--bound",type=int,required=True)
    ap.add_argument("--first-move",type=int,required=True)
    ap.add_argument("--max-nodes",type=int,default=400000)
    ap.add_argument("--max-seconds",type=int,default=3000)
    ap.add_argument("--reverse-depth",type=int,default=8)
    ap.add_argument("--reverse-cap",type=int,default=500000)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root/"andrews_curtis"))
    from solver_v2_gssub import build_reverse,total_len
    sys.path.insert(0,str(root/"acc_competitive"))
    from proof_atlas_fortify_v1 import mod_state,modular_pdb

    acc=Path(a.acc_root);sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    man=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    by={c["challenge_id"]:c for c in man["challenges"]};lim=man["limits"]
    c=by[a.challenge_id]
    initial=tuple(tuple(w) for w in c["initial_relators"])
    seed=parse(a.candidate_file,a.challenge_id)
    sv=core.verify(c,seed,c["move_spec_version"],lim)
    if not sv.get("ok"):raise RuntimeError(("bad seed",sv))

    corridor=[initial];s=initial
    for m in seed:
        s=core.apply_move(s,m);corridor.append(s)
    corridor_feats=[feat(x) for x in corridor]

    t=time.time()
    reverse,hist=build_reverse(core,a.reverse_depth,a.reverse_cap)
    reverse_s=time.time()-t

    primes=(2,3,5,7,11,13)
    pdb={p:modular_pdb(p) for p in primes}
    def lb(st):
        z=0
        for p in primes:
            d=pdb[p].get(mod_state(st,p))
            if d is not None:z=max(z,d)
        return z

    if not (0<=a.first_move<core.NUM_MOVES):
        raise ValueError(a.first_move)
    start=core.apply_move(initial,a.first_move)
    if total_len(start)>lim["max_total_relator_length"]:
        out={"found":False,"status":"INVALID_FIRST_MOVE_BY_LIMIT","first_move":a.first_move}
        Path(a.out_dir).mkdir(parents=True,exist_ok=True)
        Path(a.out_dir,"result.json").write_text(json.dumps(out,indent=2)+"\n")
        return

    k0=key_state(start)
    best={k0:1};parent={k0:(None,a.first_move)}
    states={k0:start}
    serial=0
    def shape(st):
        f=feat(st)
        return min(fd(f,q) for q in corridor_feats)
    def jitter(k):
        # deterministic, tiny tie diversity between structurally equal states
        return ((sum((i+1)*b for i,b in enumerate(k)) + 97*a.first_move)%1000)/1000.0
    def priority(st,g,k):
        # pruning remains only certified bound g+lb<=bound
        return (g+lb(st), 0.35*total_len(st)+0.10*shape(st)+0.001*jitter(k))
    pq=[(*priority(start,1,k0),1,serial,k0)];serial+=1
    popped=generated=pruned=0;goal=None;tail=None
    began=time.time()

    while pq and popped<a.max_nodes and time.time()-began<a.max_seconds:
        _,_,g,_,k=heapq.heappop(pq)
        if g!=best.get(k):continue
        st=states[k]
        if g+lb(st)>a.bound:
            pruned+=1;continue
        popped+=1
        suf=reverse.get(st)
        if suf is not None and g+len(suf)<=a.bound:
            goal=k;tail=tuple(suf);break
        last=parent[k][1]
        for m in range(core.NUM_MOVES):
            if core.INVERSE_MOVE[last]==m:continue
            n=core.apply_move(st,m);generated+=1
            if total_len(n)>lim["max_total_relator_length"]:continue
            ng=g+1
            if ng+lb(n)>a.bound:
                pruned+=1;continue
            nk=key_state(n)
            if ng>=best.get(nk,10**9):continue
            best[nk]=ng;states[nk]=n;parent[nk]=(k,m)
            p1,p2=priority(n,ng,nk)
            heapq.heappush(pq,(p1,p2,ng,serial,nk));serial+=1

    path=None;verdict=None
    if goal is not None:
        pre=[];cur=goal
        while parent[cur][0] is not None:
            prev,m=parent[cur];pre.append(m);cur=prev
        pre.append(a.first_move);pre.reverse()
        path=pre+list(tail)
        verdict=core.verify(c,path,c["move_spec_version"],lim)
        if not verdict.get("ok"):raise RuntimeError(("verify",verdict,path))
        if len(path)>a.bound:raise RuntimeError(("bound",len(path),a.bound))

    status=("VERIFIED_RECORD_LENGTH_OR_BETTER" if path is not None else
            "UNKNOWN_SEARCH_NODE_CAP" if popped>=a.max_nodes else
            "UNKNOWN_SEARCH_TIME_CAP" if time.time()-began>=a.max_seconds else
            "NO_PATH_IN_EXPLORED_SCOPE")
    out={
      "experiment":"ACC_RECORD_REPRODUCTION_SHARD_V1",
      "challenge_id":a.challenge_id,"first_move":a.first_move,"bound":a.bound,
      "status":status,"found":path is not None,"length":None if path is None else len(path),
      "certificate":path,"certificate_hash":None if verdict is None else verdict.get("certificate_hash"),
      "nodes_popped":popped,"generated":generated,"pruned":pruned,"states":len(best),
      "reverse_states":len(reverse),"reverse_hist":hist,"reverse_seconds":round(reverse_s,3),
      "search_seconds":round(time.time()-began,3),"max_nodes":a.max_nodes,
      "claim_boundary":"Public record length only; no competitor path. Exact official moves and official replay."
    }
    outdir=Path(a.out_dir);outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    (outdir/"candidate.txt").write_text(
        "" if path is None else f"{a.challenge_id}: {json.dumps(path,separators=(',',':'))}\n")
    print("RECORD_SHARD",json.dumps({k:out[k] for k in (
        "first_move","bound","status","found","length","nodes_popped","states","search_seconds"
    )},sort_keys=True),flush=True)

if __name__=="__main__":main()

#!/usr/bin/env python3
import argparse,json,re,sys
from collections import deque
from pathlib import Path

def parse_submission(path,cid):
    for line in Path(path).read_text().splitlines():
        m=re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$",line.strip())
        if m and m.group(1)==cid:
            return list(json.loads(m.group(2)))
    raise KeyError(cid)

def replay_states(core,initial,path):
    states=[initial]
    s=initial
    for m in path:
        s=core.apply_move(s,m)
        states.append(s)
    return states

def bounded_paths(core,start,depth,total_cap):
    seen={start:()}
    frontier=[start]
    for _ in range(depth):
        nxt=[]
        for s in frontier:
            p=seen[s]
            for m in range(core.NUM_MOVES):
                t=core.apply_move(s,m)
                if sum(map(len,t))>total_cap or t in seen:
                    continue
                seen[t]=p+(m,)
                nxt.append(t)
        frontier=nxt
    return seen

def shorter_path(core,start,target,max_len,total_cap):
    if start==target:return []
    if max_len<=0:return None
    d1=max_len//2
    d2=max_len-d1
    f=bounded_paths(core,start,d1,total_cap)
    b=bounded_paths(core,target,d2,total_cap)
    best=None
    for meet,p1 in f.items():
        p2=b.get(meet)
        if p2 is None:continue
        tail=tuple(core.INVERSE_MOVE[m] for m in reversed(p2))
        cand=list(p1+tail)
        if len(cand)<=max_len and (best is None or len(cand)<len(best)):
            best=cand
    return best

def optimize(core,initial,path,total_cap,target_len,max_window=5,max_passes=4):
    p=list(path)
    savings=[]
    for pass_no in range(1,max_passes+1):
        changed=False
        states=replay_states(core,initial,p)
        for w in range(max_window,2,-1):
            i=0
            while i+w<=len(p):
                start=states[i]; target=states[i+w]
                rep=shorter_path(core,start,target,w-1,total_cap)
                if rep is not None and len(rep)<w:
                    old=p[i:i+w]
                    p=p[:i]+rep+p[i+w:]
                    savings.append({"pass":pass_no,"index":i,"old_len":w,"new_len":len(rep),"saved":w-len(rep)})
                    changed=True
                    states=replay_states(core,initial,p)
                    i=max(0,i-2)
                    if len(p)<target_len:
                        return p,savings
                else:
                    i+=1
        if not changed:
            break
    return p,savings

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--candidate-file",required=True)
    ap.add_argument("--challenge-id",required=True)
    ap.add_argument("--frozen-best",type=int,required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--max-window",type=int,default=5)
    a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; byid={c["challenge_id"]:c for c in manifest["challenges"]}
    c=byid[a.challenge_id]
    initial=tuple(tuple(w) for w in c["initial_relators"])
    old=parse_submission(a.candidate_file,a.challenge_id)
    ov=core.verify(c,old,c["move_spec_version"],limits)
    if not ov.get("ok"):raise RuntimeError("input candidate fails official verifier")

    target_len=a.frozen_best
    new,changes=optimize(core,initial,old,limits["max_total_relator_length"],target_len,a.max_window)
    nv=core.verify(c,new,c["move_spec_version"],limits)
    if not nv.get("ok"):raise RuntimeError("optimized candidate fails official verifier")

    sid="sac-"+a.challenge_id[3:]; sc=byid[sid]; stable=new+[16,15]
    sv=stable_core.verify(sc,stable,sc["move_spec_version"],limits)
    if not sv.get("ok"):raise RuntimeError("stable derivative fails")

    rows=[
      f"{a.challenge_id}: {json.dumps(new,separators=(',',':'))}",
      f"{sid}: {json.dumps(stable,separators=(',',':'))}"
    ]
    (out/"pending_submission.txt").write_text("\n".join(rows)+"\n")
    rep={
      "challenge_id":a.challenge_id,"old_length":len(old),"new_length":len(new),
      "moves_saved":len(old)-len(new),"frozen_best":a.frozen_best,
      "strictly_better_frozen":len(new)<a.frozen_best,
      "changes":changes,"ac_hash":nv["certificate_hash"],"stable_hash":sv["certificate_hash"]
    }
    (out/"report.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
    print("PEEPHOLE",json.dumps({k:v for k,v in rep.items() if k!="changes"},sort_keys=True))

if __name__=="__main__":main()

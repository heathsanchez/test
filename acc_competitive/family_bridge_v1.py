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

def bidir(core,src,dst,moves,half_depth,total_cap):
    if src==dst:return []
    f={src:()}
    b={dst:()}
    fq=[src]; bq=[dst]

    def expand(front, own, other, forward):
        new=[]
        for s in front:
            p=own[s]
            for m in moves:
                n=core.apply_move(s,m)
                if sum(map(len,n))>total_cap or n in own:
                    continue
                np=p+(m,)
                own[n]=np
                if n in other:
                    if forward:
                        tail=other[n]
                        tail_inv=tuple(core.INVERSE_MOVE[x] for x in reversed(tail))
                        return np+tail_inv, []
                    else:
                        head=other[n]
                        np_inv=tuple(core.INVERSE_MOVE[x] for x in reversed(np))
                        return head+np_inv, []
                new.append(n)
        return None,new

    for _ in range(half_depth):
        hit,fq=expand(fq,f,b,True)
        if hit is not None:return list(hit)
        hit,bq=expand(bq,b,f,False)
        if hit is not None:return list(hit)
    return None

def replay(core,state,path):
    s=state
    for m in path:s=core.apply_move(s,m)
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--p9-solution",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--half-depth",type=int,default=7)
    ap.add_argument("--extra-total",type=int,default=12)
    a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"]; byid={c["challenge_id"]:c for c in manifest["challenges"]}

    ids=["ac-09633","ac-01821","ac-01684"]
    states={cid:tuple(tuple(w) for w in byid[cid]["initial_relators"]) for cid in ids}
    p9=parse_submission(a.p9_solution,"ac-09633")
    assert core.verify(byid["ac-09633"],p9,byid["ac-09633"]["move_spec_version"],limits)["ok"]

    configs=[
      ("r1_only",[1,4,5,10,11,12,13]),
      ("full",list(range(core.NUM_MOVES))),
    ]
    bridges={}
    evidence=[]
    for src,dst in (("ac-01821","ac-09633"),("ac-01684","ac-01821")):
        cap=max(sum(map(len,states[src])),sum(map(len,states[dst])))+a.extra_total
        found=None
        for name,moves in configs:
            path=bidir(core,states[src],states[dst],moves,a.half_depth,cap)
            evidence.append({"src":src,"dst":dst,"config":name,"found":path is not None,
                             "length":None if path is None else len(path),"cap":cap})
            if path is not None:
                if replay(core,states[src],path)!=states[dst]:
                    raise RuntimeError("bridge replay mismatch")
                found=path;break
        bridges[(src,dst)]=found

    candidates={}
    b10=bridges[("ac-01821","ac-09633")]
    if b10 is not None:
        candidates["ac-01821"]=b10+p9
    b11=bridges[("ac-01684","ac-01821")]
    if b11 is not None and b10 is not None:
        candidates["ac-01684"]=b11+b10+p9

    rows=[]
    lines=[]
    for cid,path in candidates.items():
        c=byid[cid]
        v=core.verify(c,path,c["move_spec_version"],limits)
        sid="sac-"+cid[3:]; sc=byid[sid]
        sp=path+[16,15]
        sv=stable_core.verify(sc,sp,sc["move_spec_version"],limits)
        if not v.get("ok") or not sv.get("ok"):
            raise RuntimeError(f"candidate verify fail {cid}")
        rows.append({"challenge_id":cid,"length":len(path),"stable_length":len(sp),
                     "bridge_10_len":None if b10 is None else len(b10),
                     "bridge_11_len":None if b11 is None else len(b11),
                     "ac_hash":v["certificate_hash"],"stable_hash":sv["certificate_hash"]})
        lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
        lines.append(f"{sid}: {json.dumps(sp,separators=(',',':'))}")

    (out/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    (out/"candidates.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text("\n".join(lines)+("\n" if lines else ""))
    rep={"half_depth":a.half_depth,"bridge_10":None if b10 is None else len(b10),
         "bridge_11":None if b11 is None else len(b11),"candidate_count":len(rows),
         "candidates":[{"id":r["challenge_id"],"length":r["length"]} for r in rows]}
    (out/"report.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
    print("FAMILY_BRIDGE",json.dumps(rep,sort_keys=True))

if __name__=="__main__":main()

#!/usr/bin/env python3
import argparse,collections,json,sqlite3,sys
from pathlib import Path

TARGET=((1,),(2,))
MAP={-2:1,-1:2,1:3,2:4}

def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])

def load_atlas(path):
    db=sqlite3.connect(path)
    dist={bytes(k):int(d) for k,d in db.execute("SELECT state,distance FROM atlas")}
    return db,dist

def atlas_suffix(core,db,state,limit):
    s=state;out=[];seen={s}
    for _ in range(max(0,limit)):
        if s==TARGET:return out
        row=db.execute("SELECT next_move FROM atlas WHERE state=?",(key_state(s),)).fetchone()
        if row is None or row[0] is None:return None
        m=int(row[0]);out.append(m);s=core.apply_move(s,m)
        if s in seen:return None
        seen.add(s)
    return out if s==TARGET else None

def connect(core,initial,atlas_dist,db,ceiling,depth_limit,total_cap,node_cap):
    initial=tuple(tuple(w) for w in initial)
    q=collections.deque([(initial,0,None)])
    parent={initial:(None,None)}
    best=None
    nodes=0
    while q and nodes<node_cap:
        s,g,last=q.popleft();nodes+=1
        ad=atlas_dist.get(key_state(s))
        if ad is not None:
            total=g+ad
            if total<ceiling and (best is None or total<best[0]):
                best=(total,s,g)
        if g>=depth_limit:continue
        if best is not None and g+1>=best[0]:continue
        for m in range(core.NUM_MOVES):
            if last is not None and core.INVERSE_MOVE[last]==m:continue
            n=core.apply_move(s,m)
            if sum(map(len,n))>total_cap or n in parent:continue
            parent[n]=(s,m);q.append((n,g+1,m))
    if best is None:return None,{"nodes":nodes,"node_cap_hit":nodes>=node_cap}
    _,hit,g=best
    prefix=[];s=hit
    while parent[s][0] is not None:
        prev,m=parent[s];prefix.append(m);s=prev
    prefix.reverse()
    suffix=atlas_suffix(core,db,hit,ceiling-len(prefix)+1)
    if suffix is None:return None,{"nodes":nodes,"hit":True,"suffix_fail":True,"node_cap_hit":nodes>=node_cap}
    return prefix+suffix,{"nodes":nodes,"prefix":len(prefix),"suffix":len(suffix),"atlas_distance":len(suffix),"node_cap_hit":nodes>=node_cap}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--atlas",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--target-ids-file",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--connector-depth",type=int,default=4)
    ap.add_argument("--node-cap",type=int,default=60000)
    ap.add_argument("--allow-unsolved",action="store_true")
    a=ap.parse_args()

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"];byid={c["challenge_id"]:c for c in manifest["challenges"]}
    snap=json.loads(Path(a.snapshot_ac).read_text());d=snap.get("data",snap)
    live={str(cid):x for x in d["items"] if isinstance(x,dict)
          for cid in [x.get("problemId") or x.get("challengeId")] if cid is not None}
    targets=json.loads(Path(a.target_ids_file).read_text())
    targets=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in targets]

    db,atlas_dist=load_atlas(a.atlas)
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[];lines=[]
    for cid in targets:
        c=byid.get(cid);row=live.get(cid,{})
        if c is None or not cid.startswith("ac-"):continue
        incumbent=row.get("currentBestLength")
        solved=isinstance(incumbent,int) and row.get("status")=="solved" and (row.get("kTeams") or 0)>0
        unsolved=not solved and (row.get("status")!="solved" or (row.get("kTeams") or 0)==0 or incumbent is None)
        if solved:
            ceiling=incumbent
        elif a.allow_unsolved and unsolved:
            ceiling=int(limits["max_path_length"])+1
            incumbent=None
        else:
            continue
        path,meta=connect(core,c["initial_relators"],atlas_dist,db,ceiling,a.connector_depth,
                          int(limits["max_total_relator_length"]),a.node_cap)
        rec={"challenge_id":cid,"live_status":"solved" if solved else "unsolved","incumbent":incumbent,**meta}
        if path is not None:
            v=core.verify(c,path,c["move_spec_version"],limits)
            if not v.get("ok"):raise RuntimeError(f"connector verifier fail {cid}: {v}")
            scoring_gain=(incumbent is None) or len(path)<incumbent
            rec.update({"found":True,"length":len(path),"scoring_gain":scoring_gain,
                        "strict_win":bool(incumbent is not None and len(path)<incumbent),
                        "new_solve":incumbent is None,"work":v.get("work"),
                        "certificate_hash":v.get("certificate_hash")})
            if scoring_gain:
                lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
        else:
            rec.update({"found":False,"scoring_gain":False,"strict_win":False,"new_solve":False})
        rows.append(rec)
        print("CONNECTOR_CASE",json.dumps(rec,sort_keys=True))

    (out/"results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text("\n".join(lines)+("\n" if lines else ""))
    summary={"targets":len(rows),"unsolved_targets":sum(r["live_status"]=="unsolved" for r in rows),
             "gains":sum(r["scoring_gain"] for r in rows),"new_solves":sum(r["new_solve"] for r in rows),
             "strict_wins":sum(r["strict_win"] for r in rows),"atlas_states":len(atlas_dist),
             "pending_rows":len(lines),"connector_depth":a.connector_depth,"node_cap":a.node_cap}
    (out/"report.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("CONNECTOR_SUMMARY",json.dumps(summary,sort_keys=True))
    db.close()

if __name__=="__main__":main()

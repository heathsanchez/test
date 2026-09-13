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
    for _ in range(limit):
        if s==TARGET:return out
        row=db.execute("SELECT next_move FROM atlas WHERE state=?",(key_state(s),)).fetchone()
        if row is None or row[0] is None:return None
        m=int(row[0]);out.append(m);s=core.apply_move(s,m)
        if s in seen:return None
        seen.add(s)
    return None

def connect(core,initial,atlas_dist,db,incumbent,depth_limit,total_cap,node_cap):
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
            if total<incumbent and (best is None or total<best[0]):
                best=(total,s,g)
        if g>=depth_limit:continue
        if best is not None and g+1>=best[0]:continue
        for m in range(core.NUM_MOVES):
            if last is not None and core.INVERSE_MOVE[last]==m:continue
            n=core.apply_move(s,m)
            if sum(map(len,n))>total_cap or n in parent:continue
            parent[n]=(s,m);q.append((n,g+1,m))
    if best is None:return None,{"nodes":nodes}
    _,hit,g=best
    prefix=[]
    s=hit
    while parent[s][0] is not None:
        prev,m=parent[s];prefix.append(m);s=prev
    prefix.reverse()
    suffix=atlas_suffix(core,db,hit,incumbent-len(prefix)+8)
    if suffix is None:return None,{"nodes":nodes,"hit":True,"suffix_fail":True}
    return prefix+suffix,{"nodes":nodes,"prefix":len(prefix),"suffix":len(suffix),"atlas_distance":len(suffix)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--atlas",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--target-ids-file",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--connector-depth",type=int,default=4)
    ap.add_argument("--node-cap",type=int,default=60000)
    a=ap.parse_args()

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"];byid={c["challenge_id"]:c for c in manifest["challenges"]}
    snap=json.loads(Path(a.snapshot_ac).read_text());d=snap.get("data",snap)
    live={x["challengeId"]:x for x in d["items"]}
    targets=json.loads(Path(a.target_ids_file).read_text())
    targets=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in targets]

    db,atlas_dist=load_atlas(a.atlas)
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[];lines=[]
    for cid in targets:
        c=byid.get(cid);row=live.get(cid,{})
        if c is None:continue
        best=row.get("currentBestLength")
        if not isinstance(best,int):continue
        path,meta=connect(core,c["initial_relators"],atlas_dist,db,best,a.connector_depth,
                          limits["max_total_relator_length"],a.node_cap)
        rec={"challenge_id":cid,"incumbent":best,**meta}
        if path is not None:
            v=core.verify(c,path,c["move_spec_version"],limits)
            if not v.get("ok"):raise RuntimeError(f"connector verifier fail {cid}")
            rec.update({"found":True,"length":len(path),"strict_win":len(path)<best,
                        "certificate_hash":v.get("certificate_hash")})
            if len(path)<best:
                sid="sac-"+cid[3:];sc=byid[sid];stable=path+[16,15]
                sv=stable_core.verify(sc,stable,sc["move_spec_version"],limits)
                if not sv.get("ok"):raise RuntimeError(f"stable connector verifier fail {sid}")
                lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
                lines.append(f"{sid}: {json.dumps(stable,separators=(',',':'))}")
        else:
            rec.update({"found":False,"strict_win":False})
        rows.append(rec)
        print("CONNECTOR_CASE",json.dumps(rec,sort_keys=True))

    (out/"results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text("\n".join(lines)+("\n" if lines else ""))
    summary={"targets":len(rows),"wins":sum(r["strict_win"] for r in rows),
             "atlas_states":len(atlas_dist),"pending_rows":len(lines),
             "connector_depth":a.connector_depth}
    (out/"report.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("CONNECTOR_SUMMARY",json.dumps(summary,sort_keys=True))
    db.close()

if __name__=="__main__":main()

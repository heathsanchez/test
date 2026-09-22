#!/usr/bin/env python3
import argparse,heapq,json,sqlite3,sys,time
from pathlib import Path

TARGET=((1,),(2,))
MAP={-2:1,-1:2,1:3,2:4}

def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])

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

def score_state(s,g,depth_weight):
    l0,l1=len(s[0]),len(s[1])
    total=l0+l1
    imbalance=abs(l0-l1)
    # Direct official-cost search: structural simplification is heuristic only;
    # g remains the actual official move count.
    return total + 0.20*max(l0,l1) + 0.04*imbalance + depth_weight*g

def reconstruct(parent,state):
    out=[];s=state
    while parent[s][0] is not None:
        prev,m=parent[s];out.append(m);s=prev
    out.reverse();return out

def search(core,initial,db,atlas_dist,incumbent,node_cap,time_cap,total_cap,depth_weight):
    initial=tuple(tuple(w) for w in initial)
    parent={initial:(None,None)}
    best_g={initial:0}
    heap=[(score_state(initial,0,depth_weight),0,0,initial,None)]
    serial=1;nodes=0;best=None;start=time.time()
    while heap and nodes<node_cap and time.time()-start<time_cap:
        _,g,_,s,last=heapq.heappop(heap)
        if best_g.get(s)!=g:continue
        nodes+=1

        ad=atlas_dist.get(key_state(s))
        if ad is not None:
            total=g+ad
            if total<incumbent and (best is None or total<best[0]):
                prefix=reconstruct(parent,s)
                suffix=atlas_suffix(core,db,s,incumbent-len(prefix)+16)
                if suffix is not None:
                    cand=prefix+suffix
                    if len(cand)<incumbent and (best is None or len(cand)<best[0]):
                        best=(len(cand),cand,s,g,len(suffix))
        if s==TARGET:
            cand=reconstruct(parent,s)
            if len(cand)<incumbent and (best is None or len(cand)<best[0]):
                best=(len(cand),cand,s,g,0)

        upper=best[0] if best is not None else incumbent
        if g+1>=upper:continue

        for m in range(core.NUM_MOVES):
            if last is not None and core.INVERSE_MOVE[last]==m:continue
            n=core.apply_move(s,m)
            if sum(map(len,n))>total_cap:continue
            ng=g+1
            if ng>=upper:continue
            if ng>=best_g.get(n,10**18):continue
            best_g[n]=ng;parent[n]=(s,m)
            heapq.heappush(heap,(score_state(n,ng,depth_weight),ng,serial,n,m));serial+=1

    meta={"nodes":nodes,"seconds":round(time.time()-start,3),"visited":len(best_g),
          "frontier":len(heap),"depth_weight":depth_weight}
    if best is None:return None,meta
    meta.update({"length":best[0],"prefix":best[3],"atlas_suffix":best[4]})
    return best[1],meta

def snapshot_rows(path):
    snap=json.loads(Path(path).read_text())
    d=snap.get("data",snap)
    out={}
    for x in d["items"]:
        cid=x.get("problemId") or x.get("challengeId")
        if cid:
            out[cid]=x
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--atlas",required=True)
    ap.add_argument("--snapshot-ac",required=True)
    ap.add_argument("--snapshot-stable",required=True)
    ap.add_argument("--target-ids-file",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--node-cap",type=int,default=250000)
    ap.add_argument("--time-cap",type=float,default=600)
    ap.add_argument("--depth-weight",type=float,default=0.15)
    ap.add_argument("--extra-total",type=int,default=40)
    a=ap.parse_args()

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core,stable_core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    limits=manifest["limits"];byid={c["challenge_id"]:c for c in manifest["challenges"]}
    live_ac=snapshot_rows(a.snapshot_ac)
    live_stable=snapshot_rows(a.snapshot_stable)
    targets=json.loads(Path(a.target_ids_file).read_text())
    targets=[x["challenge_id"] if isinstance(x,dict) else str(x) for x in targets]

    db=sqlite3.connect(a.atlas)
    atlas_dist={bytes(k):int(dist) for k,dist in db.execute("SELECT state,distance FROM atlas")}
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[];lines=[]
    for cid in targets:
        c=byid.get(cid);ac_row=live_ac.get(cid,{})
        if c is None:continue
        ac_incumbent=ac_row.get("currentBestLength")
        if not isinstance(ac_incumbent,int):continue
        sid="sac-"+cid[3:] if cid.startswith("ac-") else None
        stable_row=live_stable.get(sid,{}) if sid else {}
        stable_incumbent=stable_row.get("currentBestLength")
        # A source path of length L gives a Stable path of L+2 via the
        # separately pinned-verified [16,15] transport. Search to the looser
        # of the two strict-improvement bounds; publication remains track-local.
        source_bound=ac_incumbent
        if isinstance(stable_incumbent,int):
            source_bound=max(source_bound,stable_incumbent-2)

        initial=tuple(tuple(w) for w in c["initial_relators"])
        total_cap=min(limits["max_total_relator_length"],sum(map(len,initial))+a.extra_total)
        path,meta=search(core,initial,db,atlas_dist,source_bound,a.node_cap,a.time_cap,total_cap,a.depth_weight)
        rec={"challenge_id":cid,"ac_incumbent":ac_incumbent,
             "stable_challenge_id":sid,"stable_incumbent":stable_incumbent,
             "source_bound_exclusive":source_bound,"transport_cost":2,
             "transport_slack":(stable_incumbent-ac_incumbent-2)
                 if isinstance(stable_incumbent,int) else None,
             "total_cap":total_cap,**meta}
        if path is not None:
            v=core.verify(c,path,c["move_spec_version"],limits)
            if not v.get("ok"):raise RuntimeError(f"official search verify fail {cid}")
            ac_strict=len(path)<ac_incumbent
            stable_strict=False
            stable_len=None
            stable_hash=None
            if sid and isinstance(stable_incumbent,int):
                sc=byid[sid];stable=path+[16,15]
                stable_len=len(stable)
                if stable_len<stable_incumbent:
                    sv=stable_core.verify(sc,stable,sc["move_spec_version"],limits)
                    if not sv.get("ok"):raise RuntimeError(f"stable verify fail {sid}")
                    stable_hash=sv.get("certificate_hash")
                    stable_strict=True
            rec.update({"found":True,"source_length":len(path),
                        "ac_strict_win":ac_strict,"stable_strict_win":stable_strict,
                        "stable_length":stable_len,
                        "certificate_hash":v.get("certificate_hash"),
                        "stable_certificate_hash":stable_hash,
                        "strict_win":ac_strict or stable_strict})
            if ac_strict:
                lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
            if stable_strict:
                lines.append(f"{sid}: {json.dumps(path+[16,15],separators=(',',':'))}")
        else:
            rec.update({"found":False,"ac_strict_win":False,
                        "stable_strict_win":False,"strict_win":False})
        rows.append(rec);print("OFFICIAL_CASE",json.dumps(rec,sort_keys=True))

    (out/"results.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    (out/"pending_submission.txt").write_text("\n".join(lines)+("\n" if lines else ""))
    summary={"targets":len(rows),"winning_targets":sum(r["strict_win"] for r in rows),
             "ac_wins":sum(r.get("ac_strict_win",False) for r in rows),
             "stable_wins":sum(r.get("stable_strict_win",False) for r in rows),
             "pending_rows":len(lines),"atlas_states":len(atlas_dist),
             "nodes":sum(r.get("nodes",0) for r in rows)}
    (out/"report.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("OFFICIAL_SUMMARY",json.dumps(summary,sort_keys=True))
    db.close()

if __name__=="__main__":main()

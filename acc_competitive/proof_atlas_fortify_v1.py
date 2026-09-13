#!/usr/bin/env python3
import argparse, collections, json, sqlite3, sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from finite_group_pdb_v1 import lower_bound as finite_group_lower_bound

INV=(0,1,3,2,5,4,7,6,9,8,11,10,13,12)
TARGET=((1,),(2,))
MAP={-2:1,-1:2,1:3,2:4}
UNMAP={1:-2,2:-1,3:1,4:2}

def parse_line(line):
    line=line.strip()
    if not line or ":" not in line:return None
    cid,raw=line.split(":",1)
    try:moves=list(json.loads(raw.strip()))
    except Exception:return None
    return cid.strip(),moves

def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])

def inverse_reduce(xs):
    st=[]
    for a in xs:
        if st and st[-1]<14 and a<14 and INV[st[-1]]==a: st.pop()
        else: st.append(a)
    return st

def loop_erase(core,initial,moves):
    state=tuple(tuple(w) for w in initial)
    states=[state]; out=[]; pos={state:0}
    for m in moves:
        nxt=core.apply_move(states[-1],m)
        if nxt in pos:
            j=pos[nxt]
            for st in states[j+1:]:pos.pop(st,None)
            states=states[:j+1];out=out[:j]
        else:
            out.append(m);states.append(nxt);pos[nxt]=len(out)
    return out

def compress(core,initial,moves):
    cur=list(moves)
    while True:
        nxt=inverse_reduce(cur)
        nxt=loop_erase(core,initial,nxt)
        nxt=inverse_reduce(nxt)
        if len(nxt)==len(cur):return nxt
        cur=nxt

def replay_states(core,initial,moves):
    s=tuple(tuple(w) for w in initial); out=[s]
    for m in moves:
        s=core.apply_move(s,m);out.append(s)
    return out

def init_db(path):
    db=sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("""CREATE TABLE IF NOT EXISTS atlas(
      state BLOB PRIMARY KEY,
      distance INTEGER NOT NULL,
      next_move INTEGER,
      source TEXT
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS atlas_dist ON atlas(distance)")
    db.execute("INSERT OR IGNORE INTO atlas(state,distance,next_move,source) VALUES(?,?,?,?)",
               (key_state(TARGET),0,None,"target"))
    db.commit()
    return db

def get_row(db,state):
    return db.execute("SELECT distance,next_move FROM atlas WHERE state=?",(key_state(state),)).fetchone()

def upsert(db,state,distance,next_move,source):
    k=key_state(state)
    row=db.execute("SELECT distance FROM atlas WHERE state=?",(k,)).fetchone()
    if row is None or distance<row[0]:
        db.execute("INSERT INTO atlas(state,distance,next_move,source) VALUES(?,?,?,?) "
                   "ON CONFLICT(state) DO UPDATE SET distance=excluded.distance,next_move=excluded.next_move,source=excluded.source",
                   (k,int(distance),None if next_move is None else int(next_move),source))
        return True
    return False

def build_reverse_atlas(core,db,depth_limit=7,cap=250000,max_total=34):
    q=collections.deque([(TARGET,0)])
    seen={TARGET}
    inserted=0
    while q and len(seen)<cap:
        s,d=q.popleft()
        if d>=depth_limit:continue
        for m in range(core.NUM_MOVES):
            n=core.apply_move(s,m)
            if sum(map(len,n))>max_total or n in seen:continue
            seen.add(n)
            upsert(db,n,d+1,core.INVERSE_MOVE[m],"reverse-bfs")
            inserted+=1
            q.append((n,d+1))
            if len(seen)>=cap:break
    db.commit()
    return {"states":len(seen),"inserted":inserted,"depth_limit":depth_limit,"cap":cap,"max_total":max_total}

def ingest_path(core,db,cid,initial,moves,passes=2):
    states=replay_states(core,initial,moves)
    changed=0
    for _ in range(passes):
        for i in range(len(moves)-1,-1,-1):
            nxt=states[i+1]
            row=get_row(db,nxt)
            dist=(1+row[0]) if row is not None else (len(moves)-i)
            if upsert(db,states[i],dist,moves[i],cid):changed+=1
    return changed

def reconstruct(core,db,initial,max_steps):
    s=tuple(tuple(w) for w in initial)
    row=get_row(db,s)
    if row is None:return None
    moves=[]; seen={s}
    for _ in range(max_steps):
        if s==TARGET:return moves
        row=get_row(db,s)
        if row is None or row[1] is None:return None
        m=int(row[1]); moves.append(m); s=core.apply_move(s,m)
        if s in seen:return None
        seen.add(s)
    return None

def mod_state(initial,p):
    def exps(w):
        x=sum(1 if a==1 else -1 if a==-1 else 0 for a in w)%p
        y=sum(1 if a==2 else -1 if a==-2 else 0 for a in w)%p
        return x,y
    a,b=exps(initial[0]);c,d=exps(initial[1])
    return (a,b,c,d)

def mod_step(s,m,p):
    a,b,c,d=s
    if m==0:return((-a)%p,(-b)%p,c,d)
    if m==1:return(a,b,(-c)%p,(-d)%p)
    if m==2:return((a+c)%p,(b+d)%p,c,d)
    if m==3:return((a-c)%p,(b-d)%p,c,d)
    if m==4:return(a,b,(c+a)%p,(d+b)%p)
    if m==5:return(a,b,(c-a)%p,(d-b)%p)
    return s

_PDB={}
def modular_pdb(p):
    if p in _PDB:return _PDB[p]
    start=(1%p,0,0,1%p)
    q=collections.deque([start]);dist={start:0}
    while q:
        s=q.popleft();d=dist[s]
        for m in range(6):
            n=mod_step(s,m,p)
            if n not in dist:
                dist[n]=d+1;q.append(n)
    _PDB[p]=dist
    return dist

def certified_lower_bound(initial,primes=(2,3,5,7,11,13)):
    vals={}
    best=0
    for p in primes:
        d=modular_pdb(p).get(mod_state(initial,p))
        if d is not None:
            vals[str(p)]=d;best=max(best,d)
    return best,vals

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--glob",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--prior-atlas")
    ap.add_argument("--reverse-depth",type=int,default=7)
    ap.add_argument("--reverse-cap",type=int,default=250000)
    a=ap.parse_args()

    acc=Path(a.acc_root)
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    byid={c["challenge_id"]:c for c in manifest["challenges"]}
    limits=manifest["limits"]

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    atlas_path=out/"proof_atlas.sqlite"
    if a.prior_atlas and Path(a.prior_atlas).exists():
        atlas_path.write_bytes(Path(a.prior_atlas).read_bytes())
    db=init_db(atlas_path)

    raw={}
    sources={}
    for fp in sorted(Path(".").glob(a.glob)):
        for line in fp.read_text().splitlines():
            p=parse_line(line)
            if not p:continue
            cid,moves=p
            if not cid.startswith("ac-") or cid not in byid:continue
            if cid not in raw or len(moves)<len(raw[cid]):
                raw[cid]=moves;sources[cid]=str(fp)

    verified={}
    base_meta=[]
    for cid,moves in sorted(raw.items()):
        c=byid[cid]
        short=compress(core,c["initial_relators"],moves)
        v=core.verify(c,short,c["move_spec_version"],limits)
        if not v.get("ok"):
            raise RuntimeError(f"input candidate fails official verifier {cid}: {v}")
        verified[cid]=short
        base_meta.append({"challenge_id":cid,"raw":len(moves),"basic":len(short),"saved":len(moves)-len(short)})

    reverse_meta=build_reverse_atlas(core,db,a.reverse_depth,a.reverse_cap)
    for _ in range(3):
        for cid,moves in verified.items():
            ingest_path(core,db,cid,byid[cid]["initial_relators"],moves,passes=1)
        db.commit()

    optimized={}
    reports=[]
    for cid,moves in sorted(verified.items()):
        c=byid[cid]
        rec=reconstruct(core,db,c["initial_relators"],max_steps=len(moves)+32)
        if rec is None or len(rec)>len(moves):rec=moves
        rec=compress(core,c["initial_relators"],rec)
        v=core.verify(c,rec,c["move_spec_version"],limits)
        if not v.get("ok"):raise RuntimeError(f"atlas candidate fails verifier {cid}: {v}")
        mod_lb,mod_parts=certified_lower_bound(c["initial_relators"])
        fg_lb,fg_parts=finite_group_lower_bound(c["initial_relators"])
        lb=max(mod_lb,fg_lb)
        parts={"modular":mod_parts,"finite_groups":fg_parts}
        optimized[cid]=rec
        reports.append({
            "challenge_id":cid,"source":sources.get(cid),
            "input_length":len(raw[cid]),"basic_length":len(moves),
            "atlas_length":len(rec),"atlas_saved_vs_basic":len(moves)-len(rec),
            "certified_lower_bound":lb,"lower_bound_components":parts,
            "uncertified_gap_to_lower_bound":len(rec)-lb,
            "certificate_hash":v.get("certificate_hash")
        })
        ingest_path(core,db,cid,c["initial_relators"],rec,passes=2)
    db.commit()

    text="\n".join(f"{cid}: {json.dumps(m,separators=(',',':'))}" for cid,m in sorted(optimized.items()))
    if text:text+="\n"
    (out/"fortified_ac.txt").write_text(text)
    (out/"fortification.json").write_text(json.dumps(reports,indent=2,sort_keys=True)+"\n")
    db_count=db.execute("SELECT COUNT(*) FROM atlas").fetchone()[0]
    summary={
      "input_candidates":len(raw),"optimized_candidates":len(optimized),
      "total_input_moves":sum(len(x) for x in raw.values()),
      "total_output_moves":sum(len(x) for x in optimized.values()),
      "moves_saved":sum(len(raw[c])-len(optimized[c]) for c in optimized),
      "atlas_states":db_count,"reverse":reverse_meta,
      "certified_zero_gap":sum(r["uncertified_gap_to_lower_bound"]==0 for r in reports)
    }
    (out/"report.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("FORTIFY",json.dumps(summary,sort_keys=True))
    db.close()

if __name__=="__main__":main()

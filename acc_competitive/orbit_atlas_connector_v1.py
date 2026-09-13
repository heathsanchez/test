#!/usr/bin/env python3
import argparse, collections, itertools, json, sqlite3, sys
from pathlib import Path

TARGET=((1,),(2,))
MAP={-2:1,-1:2,1:3,2:4}
UNMAP={1:-2,2:-1,3:1,4:2}
GENS=(1,-1,2,-2)


def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])


def state_from_key(k):
    j=k.index(0)
    return (tuple(UNMAP[x] for x in k[:j]),tuple(UNMAP[x] for x in k[j+1:]))


def make_syms():
    out=[]
    for perm in ((1,2),(2,1)):
        for s1 in (-1,1):
            for s2 in (-1,1):
                img=(s1*perm[0],s2*perm[1])
                for swap in (False,True):
                    out.append((img,swap))
    return out

SYMS=make_syms()
SYM_INDEX={s:i for i,s in enumerate(SYMS)}


def phi_letter(img,g):
    if g>0:return img[g-1]
    return -img[-g-1]


def transform_state(s,sym):
    img,swap=sym
    a=tuple(phi_letter(img,x) for x in s[0])
    b=tuple(phi_letter(img,x) for x in s[1])
    return (b,a) if swap else (a,b)


def inverse_sym(sym):
    img,swap=sym
    inv={img[0]:1,img[1]:2,-img[0]:-1,-img[1]:-2}
    return ((inv[1],inv[2]),swap)


def compose(left,right):
    # transform(left, transform(right, state))
    li,ls=left; ri,rs=right
    img=(phi_letter(li,ri[0]),phi_letter(li,ri[1]))
    return (img,ls ^ rs)

SWAP_MOVE={0:1,1:0,2:4,3:5,4:2,5:3,
           6:10,7:11,8:12,9:13,10:6,11:7,12:8,13:9}


def map_move(m,sym):
    img,swap=sym
    if 6 <= m <= 9:
        g=GENS[m-6]; g2=phi_letter(img,g); m2=6+GENS.index(g2)
    elif 10 <= m <= 13:
        g=GENS[m-10]; g2=phi_letter(img,g); m2=10+GENS.index(g2)
    else:
        m2=m
    return SWAP_MOVE[m2] if swap else m2


def translation_table(img):
    t=list(range(256))
    for g,code in MAP.items():t[code]=MAP[phi_letter(img,g)]
    return bytes(t)

TRANS=[translation_table(s[0]) for s in SYMS]


def canonical_key_from_key(k):
    j=k.index(0)
    best=None;best_i=None
    for i,(sym,tr) in enumerate(zip(SYMS,TRANS)):
        q=k.translate(tr)
        if sym[1]:q=q[j+1:]+b'\0'+q[:j]
        if best is None or q<best:
            best=q;best_i=i
    return best,best_i


def canonical_key(s):
    return canonical_key_from_key(key_state(s))


def load_orbit_index(path):
    db=sqlite3.connect(path)
    idx={}
    raw_count=0
    for k,d in db.execute('SELECT state,distance FROM atlas'):
        raw_count+=1
        kb=bytes(k); ck,si=canonical_key_from_key(kb)
        cur=idx.get(ck)
        cand=(int(d),kb,si)
        if cur is None or cand[0]<cur[0]:idx[ck]=cand
    return db,idx,raw_count


def atlas_suffix(core,db,state,limit):
    s=state;out=[];seen={s}
    for _ in range(limit):
        if s==TARGET:return out
        row=db.execute('SELECT next_move FROM atlas WHERE state=?',(key_state(s),)).fetchone()
        if row is None or row[0] is None:return None
        m=int(row[0]);out.append(m);s=core.apply_move(s,m)
        if s in seen:return None
        seen.add(s)
    return None


def bfs_to_target(core,start,depth=10):
    if start==TARGET:return []
    q=collections.deque([start]);parent={start:(None,None)}
    while q:
        s=q.popleft()
        dep=0;u=s
        while parent[u][0] is not None:
            dep+=1;u=parent[u][0]
        if dep>=depth:continue
        for m in range(core.NUM_MOVES):
            n=core.apply_move(s,m)
            if sum(map(len,n))>12 or n in parent:continue
            parent[n]=(s,m)
            if n==TARGET:
                path=[];x=n
                while parent[x][0] is not None:
                    p,mm=parent[x];path.append(mm);x=p
                return list(reversed(path))
            q.append(n)
    return None


def build_normalizers(core):
    out={}
    for i,s in enumerate(SYMS):
        st=transform_state(TARGET,s)
        p=bfs_to_target(core,st,10)
        if p is None:raise RuntimeError(f'no target normalizer for symmetry {i}: {s} -> {st}')
        out[i]=p
    return out


def connect(core,initial,orbit_idx,db,normalizers,incumbent,depth_limit,total_cap,node_cap):
    initial=tuple(tuple(w) for w in initial)
    q=collections.deque([(initial,0,None)])
    parent={initial:(None,None)}
    best=None;nodes=0;orbit_hits=0
    while q and nodes<node_cap:
        s,g,last=q.popleft();nodes+=1
        ck,qsi=canonical_key(s)
        hit=orbit_idx.get(ck)
        if hit is not None:
            orbit_hits+=1
            ad,ak,asi=hit
            qs=SYMS[qsi];asym=SYMS[asi]
            h=compose(inverse_sym(asym),qs)  # h(s)=atlas_state
            invh=inverse_sym(h)
            ni=SYM_INDEX[invh]
            predicted=g+ad+len(normalizers[ni])
            if predicted<incumbent and (best is None or predicted<best[0]):
                best=(predicted,s,g,ak,asi,qsi,h,invh)
        if g>=depth_limit:continue
        if best is not None and g+1>=best[0]:continue
        for m in range(core.NUM_MOVES):
            if last is not None and core.INVERSE_MOVE[last]==m:continue
            n=core.apply_move(s,m)
            if sum(map(len,n))>total_cap or n in parent:continue
            parent[n]=(s,m);q.append((n,g+1,m))
    if best is None:return None,{'nodes':nodes,'orbit_hits':orbit_hits}
    _,hit,g,ak,asi,qsi,h,invh=best
    prefix=[];s=hit
    while parent[s][0] is not None:
        prev,m=parent[s];prefix.append(m);s=prev
    prefix.reverse()
    atlas_state=state_from_key(ak)
    suffix=atlas_suffix(core,db,atlas_state,incumbent-len(prefix)+32)
    if suffix is None:return None,{'nodes':nodes,'orbit_hits':orbit_hits,'hit':True,'suffix_fail':True}
    transported=[map_move(m,invh) for m in suffix]
    norm=normalizers[SYM_INDEX[invh]]
    path=prefix+transported+norm
    return path,{
        'nodes':nodes,'orbit_hits':orbit_hits,'prefix':len(prefix),
        'atlas_suffix':len(suffix),'transported_suffix':len(transported),
        'normalizer':len(norm),'query_symmetry':qsi,'atlas_symmetry':asi,
        'predicted_length':len(path)
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--target-ids-file',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--connector-depth',type=int,default=5)
    ap.add_argument('--node-cap',type=int,default=180000)
    a=ap.parse_args()

    acc=Path(a.acc_root);sys.path.insert(0,str(acc/'competition/tools'))
    from verifier import core,stable_core
    manifest=json.loads((acc/'competition/tools/verifier/data/manifest.json').read_text())
    limits=manifest['limits'];byid={c['challenge_id']:c for c in manifest['challenges']}
    snap=json.loads(Path(a.snapshot_ac).read_text());d=snap.get('data',snap)
    live={x['challengeId']:x for x in d['items']}
    targets=json.loads(Path(a.target_ids_file).read_text())
    targets=[x['challenge_id'] if isinstance(x,dict) else str(x) for x in targets]

    db,orbit_idx,raw_count=load_orbit_index(a.atlas)
    normalizers=build_normalizers(core)
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[];lines=[]
    for cid in targets:
        c=byid.get(cid);row=live.get(cid,{})
        if c is None:continue
        incumbent=row.get('currentBestLength')
        if not isinstance(incumbent,int):continue
        path,meta=connect(core,c['initial_relators'],orbit_idx,db,normalizers,incumbent,
                          a.connector_depth,limits['max_total_relator_length'],a.node_cap)
        rec={'challenge_id':cid,'incumbent':incumbent,**meta}
        if path is not None:
            v=core.verify(c,path,c['move_spec_version'],limits)
            if not v.get('ok'):
                raise RuntimeError(f'orbit connector verifier fail {cid}: {v}')
            strict=len(path)<incumbent
            rec.update({'found':True,'length':len(path),'strict_win':strict,
                        'margin':incumbent-len(path),'certificate_hash':v.get('certificate_hash')})
            if strict:
                sid='sac-'+cid[3:];sc=byid[sid];stable=path+[16,15]
                sv=stable_core.verify(sc,stable,sc['move_spec_version'],limits)
                if not sv.get('ok'):raise RuntimeError(f'stable orbit connector fail {sid}: {sv}')
                lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
                lines.append(f"{sid}: {json.dumps(stable,separators=(',',':'))}")
        else:
            rec.update({'found':False,'strict_win':False,'margin':None})
        rows.append(rec);print('ORBIT_CASE',json.dumps(rec,sort_keys=True))

    (out/'results.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (out/'pending_submission.txt').write_text('\n'.join(lines)+('\n' if lines else ''))
    summary={
      'targets':len(rows),'wins':sum(bool(r.get('strict_win')) for r in rows),
      'found':sum(bool(r.get('found')) for r in rows),'orbit_hits':sum(r.get('orbit_hits',0) for r in rows),
      'raw_atlas_states':raw_count,'orbit_classes':len(orbit_idx),'symmetry_group_size':len(SYMS),
      'effective_orbit_upper_bound':raw_count*len(SYMS),'pending_rows':len(lines),
      'connector_depth':a.connector_depth,'total_margin':sum((r.get('margin') or 0) for r in rows if r.get('strict_win'))
    }
    (out/'report.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print('ORBIT_SUMMARY',json.dumps(summary,sort_keys=True));db.close()

if __name__=='__main__':main()

#!/usr/bin/env python3
import argparse, collections, json, sqlite3, sys
from pathlib import Path

TARGET=((1,),(2,))
MAP={-2:1,-1:2,1:3,2:4}

def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])

def snapshot_rows(path):
    snap=json.loads(Path(path).read_text()); data=snap.get('data',snap); out={}
    for row in data['items']:
        cid=row.get('problemId') or row.get('challengeId')
        if cid: out[str(cid)]=row
    return out

def atlas_suffix(core,db,state,limit):
    s=state; out=[]; seen={s}
    for _ in range(max(0,limit)):
        if s==TARGET: return out
        row=db.execute('SELECT next_move FROM atlas WHERE state=?',(key_state(s),)).fetchone()
        if row is None or row[0] is None: return None
        m=int(row[0]); out.append(m); s=core.apply_move(s,m)
        if s in seen: return None
        seen.add(s)
    return out if s==TARGET else None

def connect(core,initial,atlas_dist,db,ceiling,depth_limit,total_cap,node_cap):
    initial=tuple(tuple(w) for w in initial)
    q=collections.deque([(initial,0,None)])
    parent={initial:(None,None)}; best=None; nodes=0
    while q and nodes<node_cap:
        s,g,last=q.popleft(); nodes+=1
        ad=atlas_dist.get(key_state(s))
        if ad is not None:
            total=g+ad
            if total<ceiling and (best is None or total<best[0]): best=(total,s,g)
        if g>=depth_limit: continue
        if best is not None and g+1>=best[0]: continue
        for m in range(core.NUM_MOVES):
            if last is not None and core.INVERSE_MOVE[last]==m: continue
            n=core.apply_move(s,m)
            if sum(map(len,n))>total_cap or n in parent: continue
            parent[n]=(s,m); q.append((n,g+1,m))
    if best is None:
        return None, {'nodes':nodes,'node_cap_hit':nodes>=node_cap,'frontier':len(q),'visited':len(parent)}
    _,hit,g=best
    prefix=[]; s=hit
    while parent[s][0] is not None:
        prev,m=parent[s]; prefix.append(m); s=prev
    prefix.reverse()
    suffix=atlas_suffix(core,db,hit,ceiling-len(prefix)+1)
    if suffix is None:
        return None, {'nodes':nodes,'hit':True,'suffix_fail':True,'node_cap_hit':nodes>=node_cap,'frontier':len(q),'visited':len(parent)}
    return prefix+suffix, {'nodes':nodes,'prefix':len(prefix),'suffix':len(suffix),'atlas_distance':len(suffix),'node_cap_hit':nodes>=node_cap,'frontier':len(q),'visited':len(parent)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--snapshot-stable',required=True)
    ap.add_argument('--target-ids-file',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--connector-depth',type=int,default=5)
    ap.add_argument('--node-cap',type=int,default=250000)
    a=ap.parse_args()

    acc=Path(a.acc_root); sys.path.insert(0,str(acc/'competition/tools'))
    from verifier import core, stable_core
    manifest=json.loads((acc/'competition/tools/verifier/data/manifest.json').read_text())
    limits=manifest['limits']; byid={c['challenge_id']:c for c in manifest['challenges']}
    live_ac=snapshot_rows(a.snapshot_ac); live_stable=snapshot_rows(a.snapshot_stable)
    ids_raw=json.loads(Path(a.target_ids_file).read_text())
    targets=[str(x.get('challenge_id')) if isinstance(x,dict) else str(x) for x in ids_raw]

    db=sqlite3.connect(a.atlas)
    atlas_dist={bytes(k):int(d) for k,d in db.execute('SELECT state,distance FROM atlas')}
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    rows=[]; lines=[]
    for cid in targets:
        if not cid.startswith('ac-') or cid not in byid: continue
        sid='sac-'+cid[3:]; ar=live_ac.get(cid,{}); sr=live_stable.get(sid,{})
        ab=ar.get('currentBestLength'); sb=sr.get('currentBestLength')
        if ar.get('status')!='solved' or sr.get('status')!='solved' or not isinstance(ab,int) or not isinstance(sb,int): continue
        slack=sb-ab-2
        if slack<=0: continue
        source_bound=max(ab,sb-2)
        c=byid[cid]; initial=tuple(tuple(w) for w in c['initial_relators'])
        path,meta=connect(core,initial,atlas_dist,db,source_bound,a.connector_depth,int(limits['max_total_relator_length']),a.node_cap)
        rec={'challenge_id':cid,'stable_challenge_id':sid,'ac_incumbent':ab,'stable_incumbent':sb,
             'transport_cost':2,'transport_slack':slack,'source_bound_exclusive':source_bound,
             'connector_depth':a.connector_depth,**meta}
        if path is None:
            rec.update({'found':False,'ac_strict_win':False,'stable_strict_win':False,'strict_win':False})
        else:
            v=core.verify(c,path,c['move_spec_version'],limits)
            if not v.get('ok'): raise RuntimeError(f'official AC verify fail {cid}: {v}')
            ac_win=len(path)<ab; stable=path+[16,15]; stable_win=len(stable)<sb
            stable_hash=None
            if stable_win:
                sc=byid[sid]; sv=stable_core.verify(sc,stable,sc['move_spec_version'],limits)
                if not sv.get('ok'): raise RuntimeError(f'official Stable verify fail {sid}: {sv}')
                stable_hash=sv.get('certificate_hash')
            rec.update({'found':True,'source_length':len(path),'ac_strict_win':ac_win,
                        'stable_strict_win':stable_win,'stable_length':len(stable),
                        'strict_win':ac_win or stable_win,'certificate_hash':v.get('certificate_hash'),
                        'stable_certificate_hash':stable_hash})
            if ac_win: lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
            if stable_win: lines.append(f"{sid}: {json.dumps(stable,separators=(',',':'))}")
        rows.append(rec); print('TRANSPORT_CONNECTOR_CASE',json.dumps(rec,sort_keys=True))

    (out/'results.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (out/'pending_submission.txt').write_text('\n'.join(lines)+('\n' if lines else ''))
    summary={'targets':len(rows),'winning_targets':sum(r.get('strict_win',False) for r in rows),
             'ac_wins':sum(r.get('ac_strict_win',False) for r in rows),
             'stable_wins':sum(r.get('stable_strict_win',False) for r in rows),
             'pending_rows':len(lines),'atlas_states':len(atlas_dist),'connector_depth':a.connector_depth,
             'nodes':sum(r.get('nodes',0) for r in rows)}
    (out/'report.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print('TRANSPORT_CONNECTOR_SUMMARY',json.dumps(summary,sort_keys=True)); db.close()

if __name__=='__main__': main()

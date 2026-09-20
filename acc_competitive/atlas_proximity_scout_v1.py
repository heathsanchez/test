#!/usr/bin/env python3
import argparse,collections,json,sqlite3,sys
from pathlib import Path

TARGET=((1,),(2,))
MAP={-2:1,-1:2,1:3,2:4}

def key_state(s):
    return bytes([MAP[x] for x in s[0]]+[0]+[MAP[x] for x in s[1]])

def load_ids(path):
    if not path or not Path(path).exists(): return set()
    obj=json.loads(Path(path).read_text())
    if isinstance(obj,dict):
        obj=obj.get('challenge_ids',obj.get('items',[]))
    out=set()
    for x in obj if isinstance(obj,list) else []:
        cid=x.get('challenge_id') if isinstance(x,dict) else x
        if cid: out.add(str(cid))
    return out

def atlas_suffix(core,db,state,limit):
    s=state;out=[];seen={s}
    for _ in range(max(0,limit)):
        if s==TARGET:return out
        row=db.execute('SELECT next_move FROM atlas WHERE state=?',(key_state(s),)).fetchone()
        if row is None or row[0] is None:return None
        m=int(row[0]);out.append(m);s=core.apply_move(s,m)
        if s in seen:return None
        seen.add(s)
    return out if s==TARGET else None

def shallow_hits(core,initial,atlas_dist,max_depth,total_cap,keep=8):
    initial=tuple(tuple(w) for w in initial)
    q=collections.deque([(initial,(),None)])
    seen={initial};hits=[];nodes=0
    while q:
        s,prefix,last=q.popleft();nodes+=1
        ad=atlas_dist.get(key_state(s))
        if ad is not None:
            hits.append((len(prefix)+ad,prefix,s,ad))
            hits.sort(key=lambda x:(x[0],len(x[1])))
            if len(hits)>keep:hits.pop()
        if len(prefix)>=max_depth:continue
        for m in range(core.NUM_MOVES):
            if last is not None and core.INVERSE_MOVE[last]==m:continue
            n=core.apply_move(s,m)
            if sum(map(len,n))>total_cap or n in seen:continue
            seen.add(n);q.append((n,prefix+(m,),m))
    return hits,nodes

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--attempted')
    ap.add_argument('--exclude')
    ap.add_argument('--max-depth',type=int,default=3)
    ap.add_argument('--max-targets',type=int,default=0,help='0 means all eligible fresh unsolved targets')
    a=ap.parse_args()

    acc=Path(a.acc_root);sys.path.insert(0,str(acc/'competition/tools'))
    from verifier import core
    man=json.loads((acc/'competition/tools/verifier/data/manifest.json').read_text())
    limits=man['limits'];byid={c['challenge_id']:c for c in man['challenges'] if c['challenge_id'].startswith('ac-')}
    snap=json.loads(Path(a.snapshot_ac).read_text());d=snap.get('data',snap)
    live={str(x.get('problemId') or x.get('challengeId')):x for x in d['items'] if isinstance(x,dict) and (x.get('problemId') or x.get('challengeId'))}
    blocked=load_ids(a.attempted)|load_ids(a.exclude)

    db=sqlite3.connect(a.atlas)
    atlas_dist={bytes(k):int(dist) for k,dist in db.execute('SELECT state,distance FROM atlas')}
    eligible=[]
    for cid,row in live.items():
        if cid not in byid or cid in blocked:continue
        best=row.get('currentBestLength');k=row.get('kTeams') or 0
        unsolved=row.get('status')!='solved' or k==0 or not isinstance(best,int)
        if unsolved:eligible.append(cid)
    eligible.sort()
    if a.max_targets>0:eligible=eligible[:a.max_targets]

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[];lines=[];total_nodes=0
    for i,cid in enumerate(eligible,1):
        c=byid[cid]
        hits,nodes=shallow_hits(core,c['initial_relators'],atlas_dist,a.max_depth,int(limits['max_total_relator_length']))
        total_nodes+=nodes
        rec={'challenge_id':cid,'nodes':nodes,'atlas_hits':len(hits),'found':False,'new_solve':False}
        failures=[]
        for estimate,prefix,hit,ad in hits:
            suffix=atlas_suffix(core,db,hit,ad+2)
            if suffix is None:
                failures.append({'estimate':estimate,'reason':'atlas_suffix_fail'});continue
            path=list(prefix)+suffix
            v=core.verify(c,path,c['move_spec_version'],limits)
            if not v.get('ok'):
                failures.append({'estimate':estimate,'length':len(path),'reason':v.get('error') or v.get('reason') or 'official_verify_fail'});continue
            rec.update({'found':True,'new_solve':True,'length':len(path),'prefix':len(prefix),'suffix':len(suffix),
                        'atlas_distance':ad,'work':v.get('work'),'certificate_hash':v.get('certificate_hash')})
            lines.append(f"{cid}: {json.dumps(path,separators=(',',':'))}")
            break
        if failures:rec['failed_hits']=failures
        rows.append(rec)
        if hits or rec['found']:
            print('ATLAS_PROXIMITY_CASE',json.dumps(rec,sort_keys=True))
        if i%250==0:
            print('ATLAS_PROXIMITY_PROGRESS',json.dumps({'done':i,'eligible':len(eligible),'nodes':total_nodes,'wins':len(lines)},sort_keys=True))

    (out/'results.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (out/'pending_submission.txt').write_text('\n'.join(lines)+('\n' if lines else ''))
    summary={'eligible_fresh_unsolved':len(eligible),'atlas_states':len(atlas_dist),'max_depth':a.max_depth,
             'states_checked':total_nodes,'targets_with_any_atlas_hit':sum(r['atlas_hits']>0 for r in rows),
             'verified_new_solves':sum(r['new_solve'] for r in rows),'pending_rows':len(lines),
             'excluded':len(blocked)}
    (out/'report.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print('ATLAS_PROXIMITY_SUMMARY',json.dumps(summary,sort_keys=True))
    db.close()

if __name__=='__main__':main()

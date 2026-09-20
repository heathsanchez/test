#!/usr/bin/env python3
import argparse, collections, json, sqlite3, sys
from pathlib import Path

REV={1:-2,2:-1,3:1,4:2}
GROUPS=((3,False),(3,True),(4,False),(4,True),(5,False),(5,True))


def load_ids(path):
    if not path or not Path(path).exists(): return set()
    obj=json.loads(Path(path).read_text())
    if isinstance(obj,dict): obj=obj.get('challenge_ids',obj.get('items',[]))
    out=set()
    for x in obj if isinstance(obj,list) else []:
        cid=x.get('challenge_id') if isinstance(x,dict) else x
        if cid: out.add(str(cid))
    return out


def decode_state(key):
    b=bytes(key)
    try: j=b.index(0)
    except ValueError: raise ValueError('atlas state key missing separator')
    return (tuple(REV[x] for x in b[:j]),tuple(REV[x] for x in b[j+1:]))


def multisource_distance(fg,x,y,component,sources):
    q=collections.deque(sources)
    d={s:0 for s in sources}
    while q:
        s=q.popleft(); nd=d[s]+1
        for m in range(14):
            z=fg.move(s,m,x,y)
            if z in component and z not in d:
                d[z]=nd;q.append(z)
    return d


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--attempted')
    ap.add_argument('--exclude')
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root))
    from acc_competitive import finite_group_pdb_v1 as fg

    acc=Path(a.acc_root)
    man=json.loads((acc/'competition/tools/verifier/data/manifest.json').read_text())
    byid={c['challenge_id']:c for c in man['challenges'] if c['challenge_id'].startswith('ac-')}
    snap=json.loads(Path(a.snapshot_ac).read_text()); sd=snap.get('data',snap)
    live={str(x.get('problemId') or x.get('challengeId')):x for x in sd['items']
          if isinstance(x,dict) and (x.get('problemId') or x.get('challengeId'))}
    blocked=load_ids(a.attempted)|load_ids(a.exclude)
    fresh=[]
    for cid,row in live.items():
        if cid not in byid or cid in blocked: continue
        best=row.get('currentBestLength'); k=row.get('kTeams') or 0
        if row.get('status')!='solved' or k==0 or not isinstance(best,int): fresh.append(cid)
    fresh.sort()

    db=sqlite3.connect(a.atlas)
    raw=[bytes(r[0]) for r in db.execute('SELECT state FROM atlas')]
    db.close()
    atlas_states=[decode_state(k) for k in raw]

    qdata=[]
    for n,swap in GROUPS:
        x,y,target_dist=fg.pdb(n,swap)
        component=set(target_dist)
        sources=set()
        scanned=0
        for state in atlas_states:
            scanned+=1
            p=(fg.eval_word(state[0],x,y),fg.eval_word(state[1],x,y))
            if p in component: sources.add(p)
            if len(sources)==len(component): break
        md=multisource_distance(fg,x,y,component,sources)
        # Exact sanity check for the quotient transition system: every official
        # move stays in the component and changes target distance by at most one.
        bad=0
        for s,ds in target_dist.items():
            for m in range(14):
                z=fg.move(s,m,x,y)
                dz=target_dist.get(z)
                if dz is None or abs(dz-ds)>1: bad+=1
        if bad: raise RuntimeError(f'quotient move-distance sanity failed S{n} swap={swap}: {bad}')
        label=f"S{n}:{'yx' if swap else 'xy'}"
        qdata.append((label,n,swap,x,y,component,sources,md,scanned))
        print('ATLAS_QUOTIENT',json.dumps({
            'label':label,'component_states':len(component),'atlas_projected_states':len(sources),
            'saturated':len(sources)==len(component),'atlas_rows_scanned':scanned,
            'max_distance_to_atlas_projection':max(md.values()) if md else None
        },sort_keys=True))

    rows=[]
    hist=collections.Counter()
    for cid in fresh:
        initial=byid[cid]['initial_relators']
        parts={}; finite=True
        for label,n,swap,x,y,component,sources,md,scanned in qdata:
            s=(fg.eval_word(initial[0],x,y),fg.eval_word(initial[1],x,y))
            d=md.get(s)
            parts[label]=d
            if d is None: finite=False
        lb=max((d for d in parts.values() if d is not None),default=None)
        if lb is not None: hist[lb]+=1
        rows.append({'challenge_id':cid,'atlas_quotient_lower_bound':lb,'parts':parts,'all_quotients_reachable':finite})

    rows_by_low=sorted(rows,key=lambda r:(10**9 if r['atlas_quotient_lower_bound'] is None else r['atlas_quotient_lower_bound'],r['challenge_id']))
    rows_by_high=sorted(rows,key=lambda r:(-(r['atlas_quotient_lower_bound'] if r['atlas_quotient_lower_bound'] is not None else -1),r['challenge_id']))
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    report={
      'fresh_unsolved':len(fresh),'excluded_ids':len(blocked),'atlas_states':len(atlas_states),
      'histogram':{str(k):hist[k] for k in sorted(hist)},
      'positive_lower_bound_rows':sum((r['atlas_quotient_lower_bound'] or 0)>0 for r in rows),
      'lower_bound_gt3_rows':sum((r['atlas_quotient_lower_bound'] or 0)>3 for r in rows),
      'unreachable_in_any_quotient':sum(not r['all_quotients_reachable'] for r in rows),
      'closest':rows_by_low[:25],'farthest':rows_by_high[:25],
      'quotients':[
        {'label':label,'component_states':len(component),'atlas_projected_states':len(sources),
         'saturated':len(sources)==len(component),'atlas_rows_scanned':scanned,
         'max_distance_to_atlas_projection':max(md.values()) if md else None}
        for label,n,swap,x,y,component,sources,md,scanned in qdata
      ]
    }
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('ATLAS_QUOTIENT_SUMMARY',json.dumps({k:report[k] for k in (
        'fresh_unsolved','excluded_ids','atlas_states','histogram','positive_lower_bound_rows','lower_bound_gt3_rows','unreachable_in_any_quotient')},sort_keys=True))

if __name__=='__main__': main()

#!/usr/bin/env python3
import argparse, collections, json, sqlite3, sys
from pathlib import Path

REV={1:-2,2:-1,3:1,4:2}
GROUPS=((6,False),(6,True),(7,False),(7,True))


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
    b=bytes(key);j=b.index(0)
    return (tuple(REV[x] for x in b[:j]),tuple(REV[x] for x in b[j+1:]))


def projected_distance(fg,start,sources,x,y,max_depth):
    if start in sources:return 0,1
    q=collections.deque([(start,0)]);seen={start};nodes=0
    while q:
        s,d=q.popleft();nodes+=1
        if d>=max_depth:continue
        nd=d+1
        for m in range(14):
            z=fg.move(s,m,x,y)
            if z in seen:continue
            if z in sources:return nd,nodes
            seen.add(z);q.append((z,nd))
    return None,nodes


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--attempted')
    ap.add_argument('--exclude')
    ap.add_argument('--max-depth',type=int,default=3)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from acc_competitive import finite_group_pdb_v1 as fg
    acc=Path(a.acc_root)
    man=json.loads((acc/'competition/tools/verifier/data/manifest.json').read_text())
    byid={c['challenge_id']:c for c in man['challenges'] if c['challenge_id'].startswith('ac-')}
    snap=json.loads(Path(a.snapshot_ac).read_text());sd=snap.get('data',snap)
    live={str(x.get('problemId') or x.get('challengeId')):x for x in sd['items']
          if isinstance(x,dict) and (x.get('problemId') or x.get('challengeId'))}
    blocked=load_ids(a.attempted)|load_ids(a.exclude)
    fresh=[]
    for cid,row in live.items():
        if cid not in byid or cid in blocked:continue
        best=row.get('currentBestLength');k=row.get('kTeams') or 0
        if row.get('status')!='solved' or k==0 or not isinstance(best,int):fresh.append(cid)
    fresh.sort()

    db=sqlite3.connect(a.atlas);raw=[bytes(r[0]) for r in db.execute('SELECT state FROM atlas')];db.close()
    atlas=[decode_state(k) for k in raw]
    qdata=[]
    for n,swap in GROUPS:
        t=fg.cycle(n,(0,1));c=fg.cycle(n,tuple(range(n)));x,y=(c,t) if swap else (t,c)
        sources=set()
        for s in atlas:
            sources.add((fg.eval_word(s[0],x,y),fg.eval_word(s[1],x,y)))
        label=f"S{n}:{'yx' if swap else 'xy'}"
        qdata.append((label,x,y,sources))
        print('LARGE_QUOTIENT_ATLAS',json.dumps({'label':label,'atlas_states':len(atlas),'projected_states':len(sources)},sort_keys=True))

    rows=[];hist=collections.Counter();total_nodes=0
    for i,cid in enumerate(fresh,1):
        initial=byid[cid]['initial_relators'];parts={};nodes=0
        cert_lb=0
        for label,x,y,sources in qdata:
            start=(fg.eval_word(initial[0],x,y),fg.eval_word(initial[1],x,y))
            d,nodes_i=projected_distance(fg,start,sources,x,y,a.max_depth);nodes+=nodes_i
            parts[label]=d
            lb=(a.max_depth+1) if d is None else d
            cert_lb=max(cert_lb,lb)
        total_nodes+=nodes;hist[cert_lb]+=1
        rows.append({'challenge_id':cid,'certified_atlas_distance_lb':cert_lb,'parts':parts,'projected_nodes':nodes})
        if cert_lb>1:
            print('LARGE_QUOTIENT_SEPARATOR',json.dumps(rows[-1],sort_keys=True))
        if i%250==0:
            print('LARGE_QUOTIENT_PROGRESS',json.dumps({'done':i,'eligible':len(fresh),'projected_nodes':total_nodes},sort_keys=True))

    far=sorted(rows,key=lambda r:(-r['certified_atlas_distance_lb'],r['projected_nodes'],r['challenge_id']))
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    report={
      'fresh_unsolved':len(fresh),'excluded_ids':len(blocked),'atlas_states':len(atlas),'max_depth':a.max_depth,
      'histogram':{str(k):hist[k] for k in sorted(hist)},'projected_nodes':total_nodes,
      'lb_ge_1':sum(r['certified_atlas_distance_lb']>=1 for r in rows),
      'lb_ge_2':sum(r['certified_atlas_distance_lb']>=2 for r in rows),
      'lb_ge_3':sum(r['certified_atlas_distance_lb']>=3 for r in rows),
      'lb_ge_4':sum(r['certified_atlas_distance_lb']>=4 for r in rows),
      'farthest':far[:100],
      'quotients':[{'label':label,'projected_atlas_states':len(sources)} for label,x,y,sources in qdata]
    }
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('LARGE_QUOTIENT_SUMMARY',json.dumps({k:report[k] for k in ('fresh_unsolved','atlas_states','max_depth','histogram','projected_nodes','lb_ge_1','lb_ge_2','lb_ge_3','lb_ge_4')},sort_keys=True))

if __name__=='__main__':main()

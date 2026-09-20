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
    b=bytes(key); j=b.index(0)
    return (tuple(REV[x] for x in b[:j]),tuple(REV[x] for x in b[j+1:]))


def product_project(fg,state,contexts):
    a,b=state
    return tuple((fg.eval_word(a,x,y),fg.eval_word(b,x,y)) for _,x,y in contexts)


def product_move(fg,state,m,contexts):
    return tuple(fg.move(s,m,x,y) for s,(_,x,y) in zip(state,contexts))


def product_distance(fg,start,sources,contexts,max_depth):
    if start in sources:return 0,1,[]
    q=collections.deque([(start,0,())]); seen={start}; nodes=0
    while q:
        s,d,path=q.popleft(); nodes+=1
        if d>=max_depth:continue
        nd=d+1
        for m in range(14):
            z=product_move(fg,s,m,contexts)
            if z in seen:continue
            np=path+(m,)
            if z in sources:return nd,nodes,list(np)
            seen.add(z); q.append((z,nd,np))
    return None,nodes,None


def load_prior(path):
    if not path or not Path(path).exists():return {}
    obj=json.loads(Path(path).read_text())
    if isinstance(obj,dict):obj=obj.get('rows',obj.get('items',[]))
    return {str(x['challenge_id']):x for x in obj if isinstance(x,dict) and x.get('challenge_id')}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--attempted')
    ap.add_argument('--exclude')
    ap.add_argument('--prior-rows')
    ap.add_argument('--max-depth',type=int,default=3)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
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
        if cid not in byid or cid in blocked:continue
        best=row.get('currentBestLength'); k=row.get('kTeams') or 0
        if row.get('status')!='solved' or k==0 or not isinstance(best,int):fresh.append(cid)
    fresh.sort()

    contexts=[]
    for n,swap in GROUPS:
        t=fg.cycle(n,(0,1)); c=fg.cycle(n,tuple(range(n))); x,y=(c,t) if swap else (t,c)
        contexts.append((f"S{n}:{'yx' if swap else 'xy'}",x,y))

    db=sqlite3.connect(a.atlas); raw=[bytes(r[0]) for r in db.execute('SELECT state FROM atlas')]; db.close()
    atlas=[decode_state(k) for k in raw]
    source_counts=collections.Counter(product_project(fg,s,contexts) for s in atlas)
    sources=set(source_counts)
    collisions=sum(v-1 for v in source_counts.values() if v>1)
    max_bucket=max(source_counts.values()) if source_counts else 0
    print('PRODUCT_QUOTIENT_ATLAS',json.dumps({
      'atlas_states':len(atlas),'product_signatures':len(sources),'collisions':collisions,
      'max_signature_multiplicity':max_bucket,'groups':[x[0] for x in contexts]},sort_keys=True))

    prior=load_prior(a.prior_rows)
    rows=[]; hist=collections.Counter(); total_nodes=0; regressions=[]; increased=collections.Counter()
    for i,cid in enumerate(fresh,1):
        initial=byid[cid]['initial_relators']; start=product_project(fg,initial,contexts)
        d,nodes,path=product_distance(fg,start,sources,contexts,a.max_depth)
        lb=(a.max_depth+1) if d is None else d
        total_nodes+=nodes; hist[lb]+=1
        old=prior.get(cid,{}).get('certified_atlas_distance_lb')
        if isinstance(old,int):
            if lb<old:regressions.append({'challenge_id':cid,'product_lb':lb,'independent_lb':old})
            increased[lb-old]+=1
        rec={'challenge_id':cid,'certified_product_atlas_distance_lb':lb,'product_distance':d,
             'projected_nodes':nodes,'witness_moves':path,'prior_independent_lb':old}
        rows.append(rec)
        if d is not None and d<=2:
            print('PRODUCT_QUOTIENT_NEAR',json.dumps(rec,sort_keys=True))
        if i%250==0:
            print('PRODUCT_QUOTIENT_PROGRESS',json.dumps({'done':i,'eligible':len(fresh),'projected_nodes':total_nodes},sort_keys=True))

    if regressions:
        raise RuntimeError('product quotient lower bound regressed against independent quotient: '+json.dumps(regressions[:10]))

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    near=sorted((r for r in rows if r['product_distance'] is not None),key=lambda r:(r['product_distance'],r['projected_nodes'],r['challenge_id']))
    far=sorted(rows,key=lambda r:(-r['certified_product_atlas_distance_lb'],r['projected_nodes'],r['challenge_id']))
    report={
      'version':'atlas-product-quotient-v1','read_only':True,'fresh_unsolved':len(fresh),'excluded_ids':len(blocked),
      'atlas_states':len(atlas),'product_signatures':len(sources),'signature_collisions':collisions,
      'max_signature_multiplicity':max_bucket,'max_depth':a.max_depth,'projected_nodes':total_nodes,
      'histogram':{str(k):hist[k] for k in sorted(hist)},
      'lb_ge_1':sum(r['certified_product_atlas_distance_lb']>=1 for r in rows),
      'lb_ge_2':sum(r['certified_product_atlas_distance_lb']>=2 for r in rows),
      'lb_ge_3':sum(r['certified_product_atlas_distance_lb']>=3 for r in rows),
      'lb_ge_4':sum(r['certified_product_atlas_distance_lb']>=4 for r in rows),
      'delta_vs_independent':{str(k):increased[k] for k in sorted(increased)},
      'near':near[:100],'farthest':far[:100],
      'note':'Synchronized product quotient preserves cross-quotient correlation and same-move sequences. No hit through depth d certifies exact Atlas distance > d.'
    }
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PRODUCT_QUOTIENT_SUMMARY',json.dumps({k:report[k] for k in ('fresh_unsolved','atlas_states','product_signatures','signature_collisions','max_depth','histogram','lb_ge_1','lb_ge_2','lb_ge_3','lb_ge_4','delta_vs_independent','projected_nodes')},sort_keys=True))

if __name__=='__main__':main()

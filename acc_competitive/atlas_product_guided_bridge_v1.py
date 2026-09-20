#!/usr/bin/env python3
import argparse,collections,json,sqlite3,sys
from pathlib import Path

REV={1:-2,2:-1,3:1,4:2}
TARGET=((1,),(2,))


def decode_state(key):
    b=bytes(key); j=b.index(0)
    return (tuple(REV[x] for x in b[:j]),tuple(REV[x] for x in b[j+1:]))


def reduce_word(w):
    out=[]
    for x in w:
        if out and out[-1]==-x: out.pop()
        else: out.append(x)
    return tuple(out)


def inv_word(w): return tuple(-x for x in reversed(w))


def move(s,m):
    a,b=s
    if m==0:return (inv_word(a),b)
    if m==1:return (a,inv_word(b))
    if m==2:return (reduce_word(a+b),b)
    if m==3:return (reduce_word(a+inv_word(b)),b)
    if m==4:return (a,reduce_word(b+a))
    if m==5:return (a,reduce_word(b+inv_word(a)))
    if m==6:return (reduce_word((1,)+a+(-1,)),b)
    if m==7:return (reduce_word((-1,)+a+(1,)),b)
    if m==8:return (reduce_word((2,)+a+(-2,)),b)
    if m==9:return (reduce_word((-2,)+a+(2,)),b)
    if m==10:return (a,reduce_word((1,)+b+(-1,)))
    if m==11:return (a,reduce_word((-1,)+b+(1,)))
    if m==12:return (a,reduce_word((2,)+b+(-2,)))
    if m==13:return (a,reduce_word((-2,)+b+(2,)))
    raise ValueError(m)


def atlas_suffix(hit,meta):
    s=hit; out=[]; last=meta[s][0]
    while s!=TARGET:
        dist,nm,_=meta[s]
        if nm is None: raise RuntimeError(f'missing next_move at distance {dist}')
        z=move(s,int(nm));out.append(int(nm))
        if z not in meta: raise RuntimeError('Atlas next_move leaves Atlas')
        zd=meta[z][0]
        if zd>=dist: raise RuntimeError(f'Atlas next_move not descending: {dist}->{zd}')
        s=z
        if len(out)>last+5: raise RuntimeError('Atlas suffix loop')
    return out


def search(initial,atlas,max_depth):
    if initial in atlas:return (),initial,1
    q=collections.deque([(initial,())]);seen={initial};nodes=0
    while q:
        s,path=q.popleft();nodes+=1
        if len(path)>=max_depth: continue
        for m in range(14):
            z=move(s,m)
            if z in seen: continue
            np=path+(m,)
            if z in atlas:return np,z,nodes
            seen.add(z);q.append((z,np))
    return None,None,nodes


def quotient_contexts(fg):
    out=[]
    for n,swap in ((6,False),(6,True),(7,False),(7,True)):
        t=fg.cycle(n,(0,1)); c=fg.cycle(n,tuple(range(n)))
        x,y=(c,t) if swap else (t,c)
        out.append((f"S{n}:{'yx' if swap else 'xy'}",x,y))
    # Cycle-type-distinct assignments address the verified quotient-fiber
    # coincidence residual without changing official move semantics.
    for n in (7,8):
        out.append((f'S{n}:quad-cycle',fg.cycle(n,(0,1,2,3)),fg.cycle(n,tuple(range(n)))))
    return out


def qproject(fg,state,ctxs):
    a,b=state
    return tuple((fg.eval_word(a,x,y),fg.eval_word(b,x,y)) for _,x,y in ctxs)


def qstep(fg,state,m,ctxs):
    return tuple(fg.move(s,m,x,y) for s,(_,x,y) in zip(state,ctxs))


def qdistance(fg,start,sources,ctxs,max_depth):
    if start in sources:return 0,1
    q=collections.deque([(start,0)]);seen={start};nodes=0
    while q:
        s,d=q.popleft();nodes+=1
        if d>=max_depth:continue
        nd=d+1
        for m in range(14):
            z=qstep(fg,s,m,ctxs)
            if z in seen:continue
            if z in sources:return nd,nodes
            seen.add(z);q.append((z,nd))
    return None,nodes


def exhausted_fiber_mode(a,rows,meta,byid,out):
    cert_path=Path(__file__).with_name('atlas_product_depth5_near2_exhausted_v1.json')
    if not cert_path.exists() or a.max_depth!=5:return False
    cert=json.loads(cert_path.read_text()); cert_ids=set(cert.get('challenge_ids',[]))
    ids={str(r.get('challenge_id')) for r in rows if r.get('challenge_id')}
    if not ids or not ids.issubset(cert_ids):return False
    if int(cert.get('atlas_states',-1))!=len(meta):return False

    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from acc_competitive import finite_group_pdb_v1 as fg
    ctxs=quotient_contexts(fg); base=ctxs[:4]
    base_sources=set(); refined_sources=set()
    for s in meta:
        base_sources.add(qproject(fg,s,base))
        refined_sources.add(qproject(fg,s,ctxs))
    if len(refined_sources)<=len(base_sources):
        raise RuntimeError(f'fiber refinement did not separate Atlas: {len(base_sources)}->{len(refined_sources)}')
    print('FIBER_REFINEMENT_ATLAS',json.dumps({
        'atlas_states':len(meta),'base_signatures':len(base_sources),'refined_signatures':len(refined_sources),
        'base_collisions':len(meta)-len(base_sources),'refined_collisions':len(meta)-len(refined_sources),
        'contexts':[x[0] for x in ctxs]},sort_keys=True))

    qdepth=6; results=[]; promoted=[]; total_nodes=0
    for r in rows:
        cid=r['challenge_id']; ch=byid[cid]
        initial=(tuple(ch['initial_relators'][0]),tuple(ch['initial_relators'][1]))
        d,nodes=qdistance(fg,qproject(fg,initial,ctxs),refined_sources,ctxs,qdepth)
        total_nodes+=nodes
        lb=qdepth+1 if d is None else d
        combined=max(6,lb) # certified exact depth-5 exhaustion already gives >=6.
        rec={'challenge_id':cid,'old_product_distance':r.get('product_distance'),'refined_product_distance':d,
             'refined_product_lb':lb,'combined_exact_atlas_distance_lb':combined,'projected_nodes':nodes}
        results.append(rec)
        if lb>=7:
            promoted.append(cid);print('FIBER_REFINEMENT_PROMOTION',json.dumps(rec,sort_keys=True))
    (out/'candidates.txt').write_text('')
    report={'version':'atlas-product-guided-bridge-v1/fiber-refinement','read_only':True,
            'mode':'certified-exhausted-fiber-refinement','exact_depth5_replayed':False,
            'prior_exact_lb':6,'refined_max_depth':qdepth,'targets':len(rows),'projected_nodes':total_nodes,
            'base_signatures':len(base_sources),'refined_signatures':len(refined_sources),
            'promoted_exact_lb7':len(promoted),'promoted_ids':promoted,'candidates':0,'rows':results,
            'note':'Rows already certified exact-Atlas-distance >=6 are not re-searched exactly. Two cycle-type-distinct finite-group contexts refine the synchronized quotient; no refined hit through depth 6 certifies exact Atlas distance >=7.'}
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('FIBER_REFINEMENT_SUMMARY',json.dumps({k:report[k] for k in ('targets','projected_nodes','base_signatures','refined_signatures','promoted_exact_lb7','candidates')},sort_keys=True))
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True);ap.add_argument('--atlas',required=True)
    ap.add_argument('--product-rows',required=True);ap.add_argument('--out-dir',required=True)
    ap.add_argument('--max-depth',type=int,default=4)
    a=ap.parse_args()
    man=json.loads((Path(a.acc_root)/'competition/tools/verifier/data/manifest.json').read_text())
    byid={c['challenge_id']:c for c in man['challenges']}
    rows=json.loads(Path(a.product_rows).read_text())
    targets=[r for r in rows if isinstance(r.get('product_distance'),int) and r['product_distance']<=3]

    db=sqlite3.connect(a.atlas)
    meta={}
    for state,d,nm,source in db.execute('select state,distance,next_move,source from atlas'):
        meta[decode_state(state)]=(int(d),None if nm is None else int(nm),source)
    db.close()
    if TARGET not in meta or meta[TARGET][0]!=0: raise RuntimeError('Atlas target/root invariant failed')
    checked=0
    for s,(d,nm,_) in meta.items():
        if d<=0:continue
        if nm is None:raise RuntimeError('non-root Atlas state missing next_move')
        z=move(s,nm)
        if z not in meta or meta[z][0]>=d:raise RuntimeError('Atlas descent semantics failed')
        checked+=1
        if checked>=10000:break
    print('ATLAS_DESCENT_VALIDATED',json.dumps({'checked':checked,'states':len(meta)},sort_keys=True))

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    if exhausted_fiber_mode(a,targets,meta,byid,out):return

    results=[];candidates=[];total_nodes=0
    for i,r in enumerate(targets,1):
        cid=r['challenge_id'];ch=byid[cid]
        initial=(tuple(ch['initial_relators'][0]),tuple(ch['initial_relators'][1]))
        prefix,hit,nodes=search(initial,meta,a.max_depth);total_nodes+=nodes
        rec={'challenge_id':cid,'product_distance':r['product_distance'],'nodes':nodes,'exact_bridge':prefix is not None}
        if prefix is not None:
            suffix=atlas_suffix(hit,meta);moves=list(prefix)+suffix
            rec.update({'prefix_moves':list(prefix),'atlas_hit_distance':meta[hit][0],
                        'atlas_source':meta[hit][2],'suffix_moves':suffix,'moves':moves,'length':len(moves)})
            candidates.append(rec)
            print('EXACT_BRIDGE_CANDIDATE',json.dumps(rec,sort_keys=True))
        results.append(rec)
        if i%25==0:print('EXACT_BRIDGE_PROGRESS',json.dumps({'done':i,'targets':len(targets),'nodes':total_nodes,'candidates':len(candidates)},sort_keys=True))

    sub=out/'candidates.txt'
    sub.write_text(''.join(f"{x['challenge_id']}: {json.dumps(x['moves'],separators=(',',':'))}\n" for x in candidates))
    report={'version':'atlas-product-guided-bridge-v1','read_only':True,'max_depth':a.max_depth,
            'product_near_targets':len(targets),'exact_nodes':total_nodes,'candidates':len(candidates),
            'candidate_rows':candidates,'rows':results,
            'note':'Exact BFS is restricted to rows whose synchronized S6/S7 product quotient reaches the Atlas within 3 moves; any hit is completed using the Atlas certified next_move descent.'}
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('EXACT_BRIDGE_SUMMARY',json.dumps({k:report[k] for k in ('max_depth','product_near_targets','exact_nodes','candidates')},sort_keys=True))

if __name__=='__main__':main()

#!/usr/bin/env python3
import argparse,collections,json,sqlite3
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
    # Validate the stored descent semantics before using them for any candidate.
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

    # Emit a verifier-ready file, but never publish here.
    sub=out/'candidates.txt'
    sub.write_text(''.join(f"{x['challenge_id']}: {json.dumps(x['moves'],separators=(',',':'))}\n" for x in candidates))
    report={'version':'atlas-product-guided-bridge-v1','read_only':True,'max_depth':a.max_depth,
            'product_near_targets':len(targets),'exact_nodes':total_nodes,'candidates':len(candidates),
            'candidate_rows':candidates,'rows':results,
            'note':'Exact BFS is restricted to rows whose synchronized S6/S7 product quotient reaches the Atlas within 3 moves; any hit is completed using the Atlas certified next_move descent.'}
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('EXACT_BRIDGE_SUMMARY',json.dumps({k:report[k] for k in ('max_depth','product_near_targets','exact_nodes','candidates')},sort_keys=True))

if __name__=='__main__':main()

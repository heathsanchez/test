#!/usr/bin/env python3
import argparse,json,sqlite3
from pathlib import Path

REV={1:-2,2:-1,3:1,4:2}; TARGET=((1,),(2,))

def decode_state(key):
    b=bytes(key);j=b.index(0)
    return (tuple(REV[x] for x in b[:j]),tuple(REV[x] for x in b[j+1:]))

def red(w):
    o=[]
    for x in w:
        if o and o[-1]==-x:o.pop()
        else:o.append(x)
    return tuple(o)
def inv(w):return tuple(-x for x in reversed(w))
def move(s,m):
    a,b=s
    if m==0:return(inv(a),b)
    if m==1:return(a,inv(b))
    if m==2:return(red(a+b),b)
    if m==3:return(red(a+inv(b)),b)
    if m==4:return(a,red(b+a))
    if m==5:return(a,red(b+inv(a)))
    if m==6:return(red((1,)+a+(-1,)),b)
    if m==7:return(red((-1,)+a+(1,)),b)
    if m==8:return(red((2,)+a+(-2,)),b)
    if m==9:return(red((-2,)+a+(2,)),b)
    if m==10:return(a,red((1,)+b+(-1,)))
    if m==11:return(a,red((-1,)+b+(1,)))
    if m==12:return(a,red((2,)+b+(-2,)))
    if m==13:return(a,red((-2,)+b+(2,)))
    raise ValueError(m)

def suffix(hit,meta):
    s=hit;o=[]
    while s!=TARGET:
        d,nm,src=meta[s]
        if nm is None:raise RuntimeError('missing next_move')
        z=move(s,nm)
        if z not in meta or meta[z][0]>=d:raise RuntimeError('non-descending Atlas edge')
        o.append(nm);s=z
    return o

def exact_layer4(initial,atlas):
    seen={initial};front={initial:()};generated=1
    for depth in range(1,5):
        nxt={}
        for s,p in front.items():
            for m in range(14):
                z=move(s,m)
                if z in seen:continue
                seen.add(z);np=p+(m,);nxt[z]=np;generated+=1
                if depth==4 and z in atlas:return np,z,generated
        front=nxt
    return None,None,generated

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--acc-root',required=True);ap.add_argument('--atlas',required=True)
    ap.add_argument('--product-rows',required=True);ap.add_argument('--out-dir',required=True);a=ap.parse_args()
    man=json.loads((Path(a.acc_root)/'competition/tools/verifier/data/manifest.json').read_text());byid={c['challenge_id']:c for c in man['challenges']}
    rows=json.loads(Path(a.product_rows).read_text())
    targets=[r for r in rows if r.get('product_distance') is None and int(r.get('certified_product_atlas_distance_lb',0))>=4]
    db=sqlite3.connect(a.atlas);meta={decode_state(s):(int(d),None if nm is None else int(nm),src) for s,d,nm,src in db.execute('select state,distance,next_move,source from atlas')};db.close()
    atlas=set(meta)
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    results=[];cands=[];nodes=0
    for i,r in enumerate(targets,1):
        cid=r['challenge_id'];ch=byid[cid];initial=(tuple(ch['initial_relators'][0]),tuple(ch['initial_relators'][1]))
        p,hit,n=exact_layer4(initial,atlas);nodes+=n
        rec={'challenge_id':cid,'generated':n,'exact_distance4_bridge':p is not None}
        if p is not None:
            sf=suffix(hit,meta);moves=list(p)+sf
            rec.update({'prefix_moves':list(p),'atlas_hit_distance':meta[hit][0],'atlas_source':meta[hit][2],'suffix_moves':sf,'moves':moves,'length':len(moves)})
            cands.append(rec);print('LB4_EXACT_CANDIDATE',json.dumps(rec,sort_keys=True))
        results.append(rec)
        if i%100==0:print('LB4_PROGRESS',json.dumps({'done':i,'targets':len(targets),'generated':nodes,'candidates':len(cands)},sort_keys=True))
    (out/'candidates.txt').write_text(''.join(f"{x['challenge_id']}: {json.dumps(x['moves'],separators=(',',':'))}\n" for x in cands))
    report={'version':'atlas-product-lb4-frontier-v1','read_only':True,'certified_lb4_targets':len(targets),'generated':nodes,'candidates':len(cands),'candidate_rows':cands,'rows':results,'note':'Only exact depth-4 states are tested because synchronized product quotient already certifies these targets have exact Atlas distance at least 4.'}
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('LB4_SUMMARY',json.dumps({k:report[k] for k in ('certified_lb4_targets','generated','candidates')},sort_keys=True))
if __name__=='__main__':main()

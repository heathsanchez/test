#!/usr/bin/env python3
import argparse,json,sqlite3
from pathlib import Path

REV={1:-2,2:-1,3:1,4:2}


def decode_state(key):
    b=bytes(key); j=b.index(0)
    return (tuple(REV[x] for x in b[:j]),tuple(REV[x] for x in b[j+1:]))


def reduce_word(w):
    out=[]
    for x in w:
        if out and out[-1]==-x: out.pop()
        else: out.append(x)
    return tuple(out)


def inv_word(w):
    return tuple(-x for x in reversed(w))


def apply_move(state,m):
    a,b=state
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


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--product-rows',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()

    man=json.loads((Path(a.acc_root)/'competition/tools/verifier/data/manifest.json').read_text())
    byid={c['challenge_id']:c for c in man['challenges']}
    rows=json.loads(Path(a.product_rows).read_text())

    db=sqlite3.connect(a.atlas)
    schema=[list(x) for x in db.execute('pragma table_info(atlas)')]
    raw=list(db.execute('select state from atlas'))
    atlas={decode_state(x[0]) for x in raw}
    print('ATLAS_SCHEMA',json.dumps(schema))
    print('EXACT_LIFT_ATLAS',json.dumps({'states':len(atlas)},sort_keys=True))

    tested=[];hits=[]
    for r in rows:
        path=r.get('witness_moves')
        d=r.get('product_distance')
        if path is None or d is None: continue
        cid=r['challenge_id']; ch=byid[cid]
        s=(tuple(ch['initial_relators'][0]),tuple(ch['initial_relators'][1]))
        initial=s
        max_total=sum(map(len,s)); work=max_total
        for m in path:
            s=apply_move(s,int(m))
            tot=sum(map(len,s)); max_total=max(max_total,tot); work+=tot
        hit=s in atlas
        rec={'challenge_id':cid,'product_distance':d,'witness_moves':path,'exact_hit':hit,
             'initial_shape':[len(x) for x in initial],'final_shape':[len(x) for x in s],
             'prefix_work':work,'prefix_max_total_relator_length':max_total}
        tested.append(rec)
        if hit:
            rec['exact_state']=[list(s[0]),list(s[1])]
            hits.append(rec)
            print('EXACT_LIFT_HIT',json.dumps(rec,sort_keys=True))

    bydist={}
    for r in tested:
        k=str(r['product_distance']);bydist.setdefault(k,{'tested':0,'hits':0})
        bydist[k]['tested']+=1;bydist[k]['hits']+=int(r['exact_hit'])
    report={'version':'atlas-product-exact-lift-v1','read_only':True,'atlas_states':len(atlas),
            'tested':len(tested),'hits':len(hits),'by_product_distance':bydist,
            'atlas_schema':schema,'hit_rows':hits,'tested_rows':tested,
            'note':'Applies each synchronized product-quotient witness move sequence with the pinned official AC word semantics, then tests exact resulting state membership in the Proof Atlas.'}
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('EXACT_LIFT_SUMMARY',json.dumps({k:report[k] for k in ('tested','hits','by_product_distance')},sort_keys=True))

if __name__=='__main__':main()

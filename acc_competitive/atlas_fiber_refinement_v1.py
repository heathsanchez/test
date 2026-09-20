#!/usr/bin/env python3
import argparse, base64, collections, hashlib, json, sqlite3, sys
from pathlib import Path

REV={1:-2,2:-1,3:1,4:2}


def load_ids(path):
    if not path or not Path(path).exists(): return set()
    obj=json.loads(Path(path).read_text())
    if isinstance(obj,dict) and obj.get('challenge_bitset_base64'):
        raw=base64.b64decode(obj['challenge_bitset_base64'])
        want=obj.get('challenge_bitset_sha256')
        got=hashlib.sha256(raw).hexdigest()
        if want and got != want:
            raise RuntimeError(f'challenge bitset checksum mismatch: got={got} want={want}')
        out={f'ac-{i:05d}' for i in range(len(raw)*8) if raw[i//8] & (1 << (i%8))}
        expected=obj.get('eligible_fresh_unsolved_count')
        if isinstance(expected,int) and len(out) != expected:
            raise RuntimeError(f'challenge bitset count mismatch: got={len(out)} want={expected}')
        return out
    if isinstance(obj,dict): obj=obj.get('challenge_ids',obj.get('items',[]))
    out=set()
    for x in obj if isinstance(obj,list) else []:
        cid=x.get('challenge_id') if isinstance(x,dict) else x
        if cid: out.add(str(cid))
    return out


def decode_state(key):
    b=bytes(key); j=b.index(0)
    return (tuple(REV[x] for x in b[:j]),tuple(REV[x] for x in b[j+1:]))


def contexts(fg):
    out=[]
    for n,swap in ((6,False),(6,True),(7,False),(7,True)):
        t=fg.cycle(n,(0,1)); c=fg.cycle(n,tuple(range(n)))
        x,y=(c,t) if swap else (t,c)
        out.append((f"S{n}:{'yx' if swap else 'xy'}",x,y))
    # Cycle-type-distinct assignments: exact free-group homomorphisms, not
    # simultaneous conjugates of the transposition/cycle base contexts.
    for n in (7,8):
        x=fg.cycle(n,(0,1,2,3))
        y=fg.cycle(n,tuple(range(n)))
        out.append((f"S{n}:quad-cycle",x,y))
    return out


def project(fg,state,ctxs):
    a,b=state
    return tuple((fg.eval_word(a,x,y),fg.eval_word(b,x,y)) for _,x,y in ctxs)


def step(fg,state,m,ctxs):
    return tuple(fg.move(s,m,x,y) for s,(_,x,y) in zip(state,ctxs))


def distance(fg,start,sources,ctxs,max_depth):
    if start in sources:return 0,1,[]
    q=collections.deque([(start,0,())]); seen={start}; nodes=0
    while q:
        s,d,path=q.popleft(); nodes+=1
        if d>=max_depth:continue
        nd=d+1
        for m in range(14):
            z=step(fg,s,m,ctxs)
            if z in seen:continue
            np=path+(m,)
            if z in sources:return nd,nodes,list(np)
            seen.add(z); q.append((z,nd,np))
    return None,nodes,None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--prior-rows',required=True)
    ap.add_argument('--radius4-cert',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--max-depth',type=int,default=5)
    a=ap.parse_args()

    root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root))
    from acc_competitive import finite_group_pdb_v1 as fg
    acc=Path(a.acc_root)
    man=json.loads((acc/'competition/tools/verifier/data/manifest.json').read_text())
    byid={c['challenge_id']:c for c in man['challenges'] if c['challenge_id'].startswith('ac-')}
    snap=json.loads(Path(a.snapshot_ac).read_text()); sd=snap.get('data',snap)
    live={str(x.get('problemId') or x.get('challengeId')):x for x in sd['items']
          if isinstance(x,dict) and (x.get('problemId') or x.get('challengeId'))}

    prior=json.loads(Path(a.prior_rows).read_text())
    if isinstance(prior,dict): prior=prior.get('rows',prior.get('items',[]))
    exact_r4=load_ids(a.radius4_cert)
    cohort=[]
    for r in prior if isinstance(prior,list) else []:
        cid=str(r.get('challenge_id') or '')
        d=r.get('product_distance')
        row=live.get(cid,{})
        unsolved=(row.get('status')!='solved' or (row.get('kTeams') or 0)==0)
        if cid and d in (3,4) and unsolved:
            if cid not in exact_r4:
                raise RuntimeError(f'cohort row lacks exact-radius4 certificate: {cid}')
            cohort.append((cid,d))
    cohort.sort()

    db=sqlite3.connect(a.atlas); raw=[bytes(r[0]) for r in db.execute('SELECT state FROM atlas')]; db.close()
    atlas=[decode_state(k) for k in raw]
    ctxs=contexts(fg); base=ctxs[:4]
    base_counts=collections.Counter(); refined_counts=collections.Counter()
    for s in atlas:
        base_counts[project(fg,s,base)]+=1
        refined_counts[project(fg,s,ctxs)]+=1
    base_sigs=len(base_counts); refined_sigs=len(refined_counts)
    if refined_sigs<=base_sigs:
        raise RuntimeError(f'fiber refinement failed to separate Atlas: base={base_sigs} refined={refined_sigs}')
    sources=set(refined_counts)
    print('FIBER_REFINEMENT_ATLAS',json.dumps({
      'atlas_states':len(atlas),'base_signatures':base_sigs,'refined_signatures':refined_sigs,
      'base_collisions':len(atlas)-base_sigs,'refined_collisions':len(atlas)-refined_sigs,
      'contexts':[x[0] for x in ctxs]},sort_keys=True))

    rows=[]; hist=collections.Counter(); total_nodes=0; promoted=[]
    for i,(cid,old_d) in enumerate(cohort,1):
        start=project(fg,byid[cid]['initial_relators'],ctxs)
        d,nodes,path=distance(fg,start,sources,ctxs,a.max_depth)
        lb=a.max_depth+1 if d is None else d
        # Exact radius-4 certificate already establishes exact distance >=5.
        combined_lb=max(5,lb)
        rec={'challenge_id':cid,'old_product_distance':old_d,'refined_product_distance':d,
             'refined_product_lb':lb,'combined_exact_atlas_distance_lb':combined_lb,
             'projected_nodes':nodes,'witness_moves':path}
        rows.append(rec); total_nodes+=nodes; hist[lb]+=1
        if lb>=6:
            promoted.append(cid)
            print('FIBER_REFINEMENT_PROMOTION',json.dumps(rec,sort_keys=True))
        if i%25==0:
            print('FIBER_REFINEMENT_PROGRESS',json.dumps({'done':i,'cohort':len(cohort),'nodes':total_nodes,'promoted_lb6':len(promoted)},sort_keys=True))

    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    report={
      'version':'atlas-fiber-refinement-v1','read_only':True,'atlas_states':len(atlas),
      'contexts':[x[0] for x in ctxs],'base_signatures':base_sigs,'refined_signatures':refined_sigs,
      'base_collisions':len(atlas)-base_sigs,'refined_collisions':len(atlas)-refined_sigs,
      'cohort_rule':'live unsolved rows with prior synchronized S6xS6xS7xS7 product distance 3 or 4; all exact-radius4 certified',
      'cohort_rows':len(cohort),'max_depth':a.max_depth,'projected_nodes':total_nodes,
      'histogram':{str(k):hist[k] for k in sorted(hist)},'promoted_exact_lb6':len(promoted),
      'promoted_ids':promoted,
      'claim':'Every promoted row is exact-Atlas-distance at least 6: the refined synchronized quotient has no Atlas hit through depth 5, and quotient distance is an admissible lower bound under the same official move sequence.',
      'reuse_rule':'Use the six-context synchronized quotient as a guard before any exact depth-5 bridge search on this cohort; do not spend exact depth-5 search on promoted rows against the same Atlas snapshot.'
    }
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('FIBER_REFINEMENT_SUMMARY',json.dumps({k:report[k] for k in ('atlas_states','base_signatures','refined_signatures','base_collisions','refined_collisions','cohort_rows','max_depth','histogram','promoted_exact_lb6','projected_nodes')},sort_keys=True))

if __name__=='__main__': main()

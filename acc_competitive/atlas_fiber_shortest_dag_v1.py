#!/usr/bin/env python3
import argparse, json, sqlite3, sys
from pathlib import Path

from atlas_product_guided_bridge_v1 import TARGET, atlas_suffix, decode_state, move


def contexts(fg):
    out=[]
    for n,swap in ((6,False),(6,True),(7,False),(7,True)):
        t=fg.cycle(n,(0,1)); c=fg.cycle(n,tuple(range(n)))
        x,y=(c,t) if swap else (t,c)
        out.append((f"S{n}:{'yx' if swap else 'xy'}",x,y))
    for n in (7,8):
        out.append((f'S{n}:quad-cycle',fg.cycle(n,(0,1,2,3)),fg.cycle(n,tuple(range(n)))))
    return out


def qproject(fg,state,ctxs):
    a,b=state
    return tuple((fg.eval_word(a,x,y),fg.eval_word(b,x,y)) for _,x,y in ctxs)


def qstep(fg,state,m,ctxs):
    return tuple(fg.move(s,m,x,y) for s,(_,x,y) in zip(state,ctxs))


def shortest_dag(fg,start,sources,ctxs,depth):
    layers=[{start}]
    seen={start}
    expanded=0
    for d in range(1,depth+1):
        nxt=set()
        for s in layers[-1]:
            expanded+=1
            for m in range(14):
                z=qstep(fg,s,m,ctxs)
                if z in seen:
                    continue
                seen.add(z); nxt.add(z)
        early=nxt & sources
        if d < depth and early:
            raise RuntimeError(f'quotient-distance contradiction: Atlas signature reached at depth {d} < {depth}')
        layers.append(nxt)
    hits=layers[depth] & sources
    if not hits:
        raise RuntimeError(f'expected quotient-distance-{depth} hit but found none')

    viable=[set() for _ in range(depth+1)]
    viable[depth]=hits
    reverse_checks=0
    for d in range(depth-1,-1,-1):
        want=viable[d+1]; cur=set()
        for s in layers[d]:
            for m in range(14):
                reverse_checks+=1
                if qstep(fg,s,m,ctxs) in want:
                    cur.add(s); break
        viable[d]=cur
    if start not in viable[0]:
        raise RuntimeError('shortest-path DAG lost start state')
    return layers,viable,expanded,reverse_checks


def exact_lift(initial,fg,ctxs,viable,atlas_meta):
    # Keep every distinct exact state whose projection lies on some quotient-shortest
    # path to an Atlas signature. This explores all shortest quotient lifts, not one witness.
    q0=qproject(fg,initial,ctxs)
    current={initial:(q0,())}
    counts=[1]
    for d in range(len(viable)-1):
        nxt={}
        want=viable[d+1]
        for s,(qs,path) in current.items():
            for m in range(14):
                qz=qstep(fg,qs,m,ctxs)
                if qz not in want:
                    continue
                z=move(s,m)
                if z not in nxt:
                    nxt[z]=(qz,path+(m,))
        current=nxt; counts.append(len(current))
        if not current:
            break
    exact_hits=[]
    if len(counts)==len(viable):
        for s,(qs,path) in current.items():
            if s in atlas_meta:
                exact_hits.append((s,path))
    return exact_hits,counts


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--rows',required=True)
    ap.add_argument('--depth6-cert',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--depth',type=int,default=6)
    a=ap.parse_args()
    if a.depth != 6:
        raise RuntimeError('V1 is qualified only for the newly isolated depth-6 boundary')

    root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root))
    from acc_competitive import finite_group_pdb_v1 as fg

    cert=json.loads(Path(a.depth6_cert).read_text())
    if cert.get('version')!='atlas-fiber-depth6-complete-v1':
        raise RuntimeError('unexpected depth6 certificate version')
    if int(cert.get('atlas_states',-1))!=433272:
        raise RuntimeError('unexpected certified Atlas size')
    certified={x['challenge_id'] for x in cert.get('quotient_distance6_witnesses',[])}

    rows=json.loads(Path(a.rows).read_text())
    if not isinstance(rows,list):
        raise RuntimeError('rows must be a JSON list')
    ids=[str(r.get('challenge_id') or '') for r in rows]
    if not ids or any(not x for x in ids) or not set(ids).issubset(certified):
        raise RuntimeError('row outside certified quotient-distance-6 residual')

    man=json.loads((Path(a.acc_root)/'competition/tools/verifier/data/manifest.json').read_text())
    byid={c['challenge_id']:c for c in man['challenges']}

    db=sqlite3.connect(a.atlas); meta={}
    for state,d,nm,source in db.execute('select state,distance,next_move,source from atlas'):
        meta[decode_state(state)]=(int(d),None if nm is None else int(nm),source)
    db.close()
    if len(meta)!=int(cert['atlas_states']):
        raise RuntimeError(f'Atlas size drift: {len(meta)} != {cert["atlas_states"]}')
    if TARGET not in meta or meta[TARGET][0]!=0:
        raise RuntimeError('Atlas target/root invariant failed')
    checked=0
    for s,(d,nm,_) in meta.items():
        if d<=0: continue
        if nm is None: raise RuntimeError('non-root Atlas state missing next_move')
        z=move(s,nm)
        if z not in meta or meta[z][0]>=d: raise RuntimeError('Atlas descent semantics failed')
        checked+=1
        if checked>=10000: break
    print('ATLAS_DESCENT_VALIDATED',json.dumps({'checked':checked,'states':len(meta)},sort_keys=True))

    ctxs=contexts(fg)
    sources={qproject(fg,s,ctxs) for s in meta}
    print('SHORTEST_DAG_ATLAS',json.dumps({'atlas_states':len(meta),'projected_signatures':len(sources),'contexts':[x[0] for x in ctxs]},sort_keys=True))

    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    results=[]; candidates=[]
    for i,r in enumerate(rows,1):
        cid=r['challenge_id']; ch=byid[cid]
        initial=(tuple(ch['initial_relators'][0]),tuple(ch['initial_relators'][1]))
        start=qproject(fg,initial,ctxs)
        layers,viable,expanded,reverse_checks=shortest_dag(fg,start,sources,ctxs,a.depth)
        hits,exact_counts=exact_lift(initial,fg,ctxs,viable,meta)
        rec={
            'challenge_id':cid,
            'quotient_depth':a.depth,
            'quotient_layer_sizes':[len(x) for x in layers],
            'quotient_shortest_dag_sizes':[len(x) for x in viable],
            'quotient_terminal_atlas_signatures':len(viable[-1]),
            'quotient_expanded':expanded,
            'quotient_reverse_checks':reverse_checks,
            'exact_lift_layer_sizes':exact_counts,
            'exact_atlas_hits':len(hits),
            'certified_exact_atlas_distance_lb': 7 if not hits else 6,
        }
        if hits:
            # One exact hit is enough for publication; keep the shortest completed candidate.
            completed=[]
            for hit,path in hits:
                suffix=atlas_suffix(hit,meta); moves=list(path)+suffix
                completed.append((len(moves),moves,hit,path,suffix))
            completed.sort(key=lambda x:x[0])
            _,moves,hit,path,suffix=completed[0]
            cand={'challenge_id':cid,'prefix_moves':list(path),'prefix_length':len(path),
                  'atlas_hit_distance':meta[hit][0],'atlas_source':meta[hit][2],
                  'suffix_moves':suffix,'moves':moves,'length':len(moves)}
            candidates.append(cand); rec['candidate']=cand
            print('SHORTEST_DAG_EXACT_HIT',json.dumps(cand,sort_keys=True))
        else:
            print('SHORTEST_DAG_LB7',json.dumps({'challenge_id':cid,'exact_lift_layer_sizes':exact_counts,
                  'terminal_quotient_signatures':len(viable[-1])},sort_keys=True))
        results.append(rec)
        print('SHORTEST_DAG_PROGRESS',json.dumps({'done':i,'targets':len(rows),'candidates':len(candidates)},sort_keys=True))

    (out/'candidates.txt').write_text(''.join(
        f"{x['challenge_id']}: {json.dumps(x['moves'],separators=(',',':'))}\n" for x in candidates
    ))
    report={
        'version':'atlas-fiber-shortest-dag-v1','read_only':True,
        'official_pin':cert['official_pin'],'atlas_states':len(meta),'contexts':[x[0] for x in ctxs],
        'depth':a.depth,'targets':len(results),'candidates':len(candidates),
        'certified_exact_atlas_distance_lb7':sum(1 for x in results if x['exact_atlas_hits']==0),
        'candidate_rows':candidates,'rows':results,
        'claim':'For a row whose synchronized six-context quotient distance to the Atlas is exactly 6, every exact six-move Atlas bridge must project to the quotient shortest-path DAG. Exhausting every exact lift of that full DAG therefore proves exact Atlas distance at least 7 when no exact Atlas endpoint occurs.',
        'reuse_rule':'Do not retry stored quotient witnesses or blind exact depth-6 BFS for certified rows. This result exhausts every quotient-shortest depth-6 lift against this Atlas snapshot.'
    }
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('SHORTEST_DAG_SUMMARY',json.dumps({k:report[k] for k in ('targets','candidates','certified_exact_atlas_distance_lb7')},sort_keys=True))

if __name__=='__main__': main()

#!/usr/bin/env python3
import argparse, json, sqlite3, sys
from pathlib import Path

from atlas_product_guided_bridge_v1 import TARGET, atlas_suffix, decode_state, move
from atlas_fiber_shortest_dag_v1 import contexts, qproject, qstep, exact_lift


def layered_dag(fg,start,sources,ctxs,depth):
    # Exact-length quotient layers: unlike shortest_dag, do not globally suppress
    # revisits. This retains detours/slack that can repair a non-lifting fiber.
    layers=[{start}]
    expanded=0
    for _ in range(depth):
        nxt=set()
        for s in layers[-1]:
            expanded+=1
            for m in range(14):
                nxt.add(qstep(fg,s,m,ctxs))
        layers.append(nxt)
    hits=layers[depth] & sources
    if not hits:
        return layers,[set() for _ in range(depth+1)],expanded,0
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
        raise RuntimeError('exact-length quotient DAG lost start despite terminal hit')
    return layers,viable,expanded,reverse_checks


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--rows',required=True)
    ap.add_argument('--depth5-cert',required=True)
    ap.add_argument('--shortest-dag-cert',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--depth',type=int,default=6)
    a=ap.parse_args()
    if a.depth!=6: raise RuntimeError('V1 is qualified only for the first unsearched exact depth 6')

    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from acc_competitive import finite_group_pdb_v1 as fg

    d5=json.loads(Path(a.depth5_cert).read_text())
    dagcert=json.loads(Path(a.shortest_dag_cert).read_text())
    if int(d5.get('atlas_states',-1))!=433272 or int(dagcert.get('atlas_states',-1))!=433272:
        raise RuntimeError('certificate Atlas mismatch')
    allowed=set(d5.get('exact_depth5_residual_ids',[]))
    phase=set(dagcert.get('combined_depth6_phase',{}).get('lb6_only_ids',[]))
    if allowed!=phase or len(allowed)!=28:
        raise RuntimeError('28-row slack residual mismatch')

    rows=json.loads(Path(a.rows).read_text())
    if not isinstance(rows,list): raise RuntimeError('rows must be a JSON list')
    ids=[str(r.get('challenge_id') or '') for r in rows]
    if not ids or any(not x for x in ids) or not set(ids).issubset(allowed):
        raise RuntimeError('row outside certified exact-depth5 residual')

    man=json.loads((Path(a.acc_root)/'competition/tools/verifier/data/manifest.json').read_text())
    byid={c['challenge_id']:c for c in man['challenges']}
    db=sqlite3.connect(a.atlas);meta={}
    for state,d,nm,source in db.execute('select state,distance,next_move,source from atlas'):
        meta[decode_state(state)]=(int(d),None if nm is None else int(nm),source)
    db.close()
    if len(meta)!=433272 or TARGET not in meta or meta[TARGET][0]!=0:
        raise RuntimeError('Atlas invariant failed')
    checked=0
    for s,(d,nm,_) in meta.items():
        if d<=0: continue
        if nm is None: raise RuntimeError('non-root Atlas state missing next_move')
        z=move(s,nm)
        if z not in meta or meta[z][0]>=d: raise RuntimeError('Atlas descent semantics failed')
        checked+=1
        if checked>=10000: break
    print('ATLAS_DESCENT_VALIDATED',json.dumps({'checked':checked,'states':len(meta)},sort_keys=True))

    ctxs=contexts(fg); sources={qproject(fg,s,ctxs) for s in meta}
    print('SLACK6_ATLAS',json.dumps({'atlas_states':len(meta),'projected_signatures':len(sources),'contexts':[x[0] for x in ctxs]},sort_keys=True))

    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    results=[];candidates=[]
    for i,r in enumerate(rows,1):
        cid=r['challenge_id'];ch=byid[cid]
        initial=(tuple(ch['initial_relators'][0]),tuple(ch['initial_relators'][1]))
        start=qproject(fg,initial,ctxs)
        layers,viable,expanded,reverse_checks=layered_dag(fg,start,sources,ctxs,a.depth)
        terminal=len(viable[-1])
        if terminal:
            hits,exact_counts=exact_lift(initial,fg,ctxs,viable,meta)
        else:
            hits=[];exact_counts=[1]
        rec={'challenge_id':cid,'depth':a.depth,
             'quotient_exact_length_layer_sizes':[len(x) for x in layers],
             'quotient_slack_dag_sizes':[len(x) for x in viable],
             'quotient_terminal_atlas_signatures':terminal,
             'quotient_expanded':expanded,'quotient_reverse_checks':reverse_checks,
             'exact_lift_layer_sizes':exact_counts,'exact_atlas_hits':len(hits),
             'certified_exact_atlas_distance_lb':7 if not hits else 6}
        if hits:
            completed=[]
            for hit,path in hits:
                suffix=atlas_suffix(hit,meta); moves=list(path)+suffix
                completed.append((len(moves),moves,hit,path,suffix))
            completed.sort(key=lambda x:x[0]);_,moves,hit,path,suffix=completed[0]
            cand={'challenge_id':cid,'prefix_moves':list(path),'prefix_length':len(path),
                  'atlas_hit_distance':meta[hit][0],'atlas_source':meta[hit][2],
                  'suffix_moves':suffix,'moves':moves,'length':len(moves)}
            candidates.append(cand);rec['candidate']=cand
            print('SLACK6_EXACT_HIT',json.dumps(cand,sort_keys=True))
        else:
            print('SLACK6_LB7',json.dumps({'challenge_id':cid,'terminal_quotient_signatures':terminal,
                  'exact_lift_layer_sizes':exact_counts},sort_keys=True))
        results.append(rec)
        print('SLACK6_PROGRESS',json.dumps({'done':i,'targets':len(rows),'candidates':len(candidates)},sort_keys=True))

    (out/'candidates.txt').write_text(''.join(
        f"{x['challenge_id']}: {json.dumps(x['moves'],separators=(',',':'))}\n" for x in candidates))
    report={'version':'atlas-fiber-slack6-v1','read_only':True,'official_pin':d5['official_pin'],
            'atlas_states':len(meta),'contexts':[x[0] for x in ctxs],'depth':a.depth,
            'targets':len(results),'candidates':len(candidates),
            'certified_exact_atlas_distance_lb7':sum(1 for x in results if x['exact_atlas_hits']==0),
            'candidate_rows':candidates,'rows':results,
            'claim':'The input rows are already exact-Atlas-distance at least 6. Every exact six-move Atlas bridge must project to a six-move quotient path ending in an Atlas signature. The exact-length layered quotient DAG retains revisits and detours, and every exact lift of its Atlas-reaching portion is exhausted. Zero exact endpoints therefore certifies exact Atlas distance at least 7.',
            'reuse_rule':'Do not repeat exact depth<=6, stored-witness, local-holonomy, shortest-DAG, or six-move quotient-slack lifting for certified rows against this Atlas.'}
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('SLACK6_SUMMARY',json.dumps({k:report[k] for k in ('targets','candidates','certified_exact_atlas_distance_lb7')},sort_keys=True))

if __name__=='__main__': main()

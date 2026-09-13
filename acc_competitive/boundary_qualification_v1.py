#!/usr/bin/env python3
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text())


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--targets',required=True)
    ap.add_argument('--snapshot',required=True)
    ap.add_argument('--runs-root',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--capabilities',nargs='+',required=True)
    a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    targets=load(a.targets)
    target_ids=[x['challenge_id'] if isinstance(x,dict) else str(x) for x in targets]
    snap=load(a.snapshot); data=snap.get('data',snap); items=data.get('items',data if isinstance(data,list) else [])
    live={x['challengeId']:x for x in items}

    bycap={}
    complete_caps=[]
    for cap in a.capabilities:
        p=Path(a.runs_root)/cap/'search_results.json'
        if p.exists():
            rows=load(p); bycap[cap]={r['challenge_id']:r for r in rows}
            complete_caps.append(cap)
        else:
            bycap[cap]={}

    rows=[]; residual_counts=Counter(); strict=[]
    for cid in target_ids:
        evid=[]
        verified=[]
        all_present=True
        for cap in a.capabilities:
            r=bycap.get(cap,{}).get(cid)
            if r is None:
                all_present=False; evid.append({'capability':cap,'status':'NOT_PROCESSED'}); continue
            q=bool(r.get('quotient_found'))
            comp=(r.get('compile') or {}).get('code')
            ok=bool((r.get('ac_verdict') or {}).get('ok'))
            n=r.get('atomic_length') if ok else None
            evid.append({'capability':cap,'quotient_found':q,'compile_code':comp,'verified':ok,'length':n,'nodes':r.get('nodes'),'max_nodes':r.get('max_nodes')})
            if ok and isinstance(n,int): verified.append((n,cap))
        best_live=(live.get(cid) or {}).get('currentBestLength')
        best=min(verified) if verified else None
        if best and isinstance(best_live,int) and best[0] < best_live:
            typ='STRICT_VERIFIED_WIN'; strict.append({'challenge_id':cid,'candidate_length':best[0],'live_best':best_live,'margin':best_live-best[0],'capability':best[1]})
        elif verified:
            typ='VERIFIED_BUT_NONCOMPETITIVE'
        elif not all_present:
            typ='UNKNOWN_SEARCH_INCOMPLETE_RUN'
        else:
            any_q=any(e.get('quotient_found') for e in evid)
            compile_fail=any(e.get('quotient_found') and not e.get('verified') for e in evid)
            saturated=all((e.get('nodes') or 0) >= (e.get('max_nodes') or 10**30) for e in evid)
            if compile_fail:
                typ='UNKNOWN_COMPILATION_OR_SEARCH'
            elif saturated:
                typ='UNKNOWN_SEARCH_BOUNDARY_SATURATED'
            elif any_q:
                typ='UNKNOWN_SEARCH_WITH_QUOTIENT_HIT'
            else:
                typ='UNKNOWN_SEARCH_NO_QUOTIENT_WITNESS'
        residual_counts[typ]+=1
        rows.append({'challenge_id':cid,'live_best':best_live,'best_verified_length':None if not best else best[0],'best_capability':None if not best else best[1],'typed_result':typ,'evidence':evid})

    declared_complete=(len(complete_caps)==len(a.capabilities) and all(all(cid in bycap[c] for cid in target_ids) for c in a.capabilities))
    # Constitutional point: exhausting this finite declared search portfolio does NOT certify expressive inadequacy.
    growth_authorized=False
    report={
      'experiment':'ACC_BOUNDARY_LEARNS_QUALIFICATION_V1',
      'declared_capabilities':a.capabilities,
      'targets':len(target_ids),
      'declared_portfolio_complete':declared_complete,
      'typed_results':dict(residual_counts),
      'strict_verified_wins':strict,
      'strict_win_count':len(strict),
      'expressive_inadequacy_certified':False,
      'growth_authorized':growth_authorized,
      'constitutional_result':'RETAIN_WINS_AND_RETURN_UNKNOWN_SEARCH; DO_NOT_EXPAND' if not growth_authorized else 'EXPANSION_AUTHORIZED',
      'note':'Finite portfolio exhaustion certifies only this declared bounded search portfolio. It does not by itself prove the representation/capability language expressively inadequate.'
    }
    (out/'typed_results.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (out/'strict_wins.json').write_text(json.dumps(strict,indent=2,sort_keys=True)+'\n')
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('BOUNDARY_QUALIFICATION',json.dumps(report,sort_keys=True))

if __name__=='__main__': main()

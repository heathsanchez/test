import json, sys
from collections import defaultdict
from pathlib import Path

rows=json.loads(Path(sys.argv[1]).read_text())
by=defaultdict(list)
for r in rows: by[r['arm']].append(r)
summary={}
for arm,rs in by.items():
    x={'n':len(rs),'optimal_query_rate':sum(r.get('query_optimal',False) for r in rs)/len(rs),
       'target_correct':sum(r.get('correct',False) for r in rs),
       'accuracy':sum(r.get('correct',False) for r in rs)/len(rs),
       'mean_entropy_after':sum(r.get('entropy_after',0.0) for r in rs)/len(rs)}
    if any('quotient_exact' in r for r in rs):
        qrs=[r for r in rs if 'quotient_exact' in r]
        x['exact_quotient_rate']=sum(r['quotient_exact'] for r in qrs)/len(qrs)
        x['mean_n_errors']=sum(r.get('n_errors',0) for r in qrs)/len(qrs)
    if any('rounds' in r for r in rs): x['mean_rounds']=sum(r.get('rounds',0) for r in rs)/len(rs)
    summary[arm]=x

fam=defaultdict(lambda:defaultdict(list))
for r in rows: fam[str(r['m'])][r['arm']].append(r)
by_family={}
for m,arms in fam.items():
    by_family[m]={}
    for arm,rs in arms.items():
        z={'n':len(rs),'optimal_query_rate':sum(r.get('query_optimal',False) for r in rs)/len(rs),
           'accuracy':sum(r.get('correct',False) for r in rs)/len(rs)}
        if any('quotient_exact' in r for r in rs):
            z['exact_quotient_rate']=sum(r.get('quotient_exact',False) for r in rs)/len(rs)
        by_family[m][arm]=z

v=summary['VERIFIED_SYNTHESIS']; o=summary['ONE_SHOT_SYNTHESIS']; raw=summary['RAW_DIRECT']; hand=summary['HAND_QUOTIENT']
primary={
 'verified_exact_gt_one_shot':v['exact_quotient_rate']>o['exact_quotient_rate'],
 'verified_accuracy_gt_one_shot':v['accuracy']>o['accuracy'],
 'verified_exact_ge_0p75':v['exact_quotient_rate']>=0.75,
 'verified_accuracy_ge_0p90':v['accuracy']>=0.90,
 'verified_accuracy_gt_raw':v['accuracy']>raw['accuracy'],
 'hand_accuracy_ge_0p95':hand['accuracy']>=0.95,
}
primary['primary_pass']=primary['verified_exact_gt_one_shot'] and primary['verified_accuracy_gt_one_shot']
out={'summary':summary,'by_family':by_family,'primary':primary}
Path('experiments/verified_quotient_synthesis_v1/scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))

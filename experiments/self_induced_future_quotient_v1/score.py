import json, sys
from collections import defaultdict
from pathlib import Path

p=Path(sys.argv[1]); rows=json.loads(p.read_text())
by=defaultdict(list)
for r in rows: by[r['arm']].append(r)
summary={}
for arm,rs in by.items():
    n=len(rs)
    summary[arm]={
        'n':n,
        'optimal_query_rate':sum(bool(r.get('query_optimal')) for r in rs)/n,
        'target_correct':sum(bool(r.get('correct')) for r in rs),
        'accuracy':sum(bool(r.get('correct')) for r in rs)/n,
        'mean_entropy_after':sum(float(r.get('entropy_after',0)) for r in rs)/n,
        'mean_info_gain_regret':sum(float(r.get('optimal_info_gain',0))-float(r.get('chosen_info_gain',0)) for r in rs)/n,
    }
by_family={}
for m in [2,3,5]:
    by_family[str(m)]={}
    for arm,rs in by.items():
        xs=[r for r in rs if r['m']==m]
        if xs:
            by_family[str(m)][arm]={
                'n':len(xs),
                'optimal_query_rate':sum(bool(r.get('query_optimal')) for r in xs)/len(xs),
                'accuracy':sum(bool(r.get('correct')) for r in xs)/len(xs),
                'mean_entropy_after':sum(float(r.get('entropy_after',0)) for r in xs)/len(xs),
            }
S=summary
primary={
 'self_optimal_gt_raw':S['SELF_INDUCED']['optimal_query_rate']>S['RAW_DIRECT']['optimal_query_rate'],
 'self_accuracy_gt_raw':S['SELF_INDUCED']['accuracy']>S['RAW_DIRECT']['accuracy'],
 'self_optimal_ge_0p80':S['SELF_INDUCED']['optimal_query_rate']>=0.80,
 'self_accuracy_ge_0p90':S['SELF_INDUCED']['accuracy']>=0.90,
 'hand_optimal_ge_0p90':S['HAND_QUOTIENT']['optimal_query_rate']>=0.90,
 'self_gt_sham_optimal':S['SELF_INDUCED']['optimal_query_rate']>S['SHAM_MARGINAL']['optimal_query_rate'],
}
primary['primary_pass']=primary['self_optimal_gt_raw'] and primary['self_accuracy_gt_raw']
out={'summary':summary,'by_family':by_family,'primary':primary}
(Path(__file__).parent/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
